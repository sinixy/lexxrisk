import aiohttp
import gspread
import gspread.utils
from dataclasses import dataclass

from config import TakionConfig, GSKEY_PATH, RiskConfig, FixerConfig
from common.utils import asyncify


@dataclass
class TakionUser:
    id: int
    username: str
    first_name: str
    last_name: str
    account: str

@dataclass
class DailyRisk:
    takion: TakionUser
    stop: int
    cover: int

@dataclass
class DailyFixer:
    takion: TakionUser
    trigger: int
    step: int

class RiskManager:

    def __init__(self):
        self._creds = gspread.service_account(GSKEY_PATH)

        self._risk_spreadsheet = self._creds.open_by_key(RiskConfig.KEY)
        self._risk_worksheet = self._load_sheet(self._risk_spreadsheet, RiskConfig.TITLE)

        self._fixer_spreadsheet = self._creds.open_by_key(FixerConfig.KEY)
        self._fixer_worksheet = self._load_sheet(self._fixer_spreadsheet, FixerConfig.TITLE)

    def _load_sheet(self, spreadsheet: gspread.Spreadsheet, worksheet_title: str) -> gspread.Worksheet:
        for sh in spreadsheet.worksheets():
            if sh.title == worksheet_title:
                return sh
        raise KeyError(f'No such worksheet: {worksheet_title}')
    
    async def get_takion_by_account(self, account_id: int) -> TakionUser:
        async with aiohttp.ClientSession(headers=TakionConfig.HEADERS) as session:
            async with session.get(TakionConfig.BASE_URL) as resp:
                resp.raise_for_status()
                users = await resp.json()
                for user in users:
                    if user['id'] == str(account_id):
                        return TakionUser(
                            id=user['user']['id'],
                            username=user['user']['username'],
                            first_name=user['user']['first_name'],
                            last_name=user['user']['last_name'],
                            account=user['user']['account']
                        )
                raise KeyError(f'No such takion account: {account_id}')

    @asyncify
    def get_max_risk(self, takion: TakionUser) -> DailyRisk:
        account_id = int(takion.account)
        for row in self._risk_worksheet.get(value_render_option=gspread.utils.ValueRenderOption.unformatted):
            if RiskConfig.ACCOUNT_COL >= len(row): continue
            if row[RiskConfig.ACCOUNT_COL] == account_id:
                return DailyRisk(
                    takion=takion,
                    stop=row[RiskConfig.STOP_COL],
                    cover=row[RiskConfig.COVER_COL]
                )
        raise KeyError(f'No such risk sheet account: {takion.account}')
    
    async def get_current_risk(self, takion: TakionUser) -> DailyRisk:
        async with aiohttp.ClientSession(headers=TakionConfig.HEADERS) as session:
            async with session.get(TakionConfig.BASE_URL + f'/{takion.id}') as resp:
                resp.raise_for_status()
                data = await resp.json()
                return DailyRisk(
                    takion=takion,
                    stop=data['max_loss'],
                    cover=data['max_loss_close']
                )

    async def set_stop(self, takion: TakionUser, stop: int):
        await self.set_risk(takion, stop=stop)

    async def set_cover(self, takion: TakionUser, cover: int):
        await self.set_risk(takion, cover=cover)

    async def set_risk(self, takion: TakionUser, stop: int = None, cover: int = None):
        payload = {}
        if stop: payload['max_loss'] = stop
        if cover: payload['max_loss_close'] = cover
        if not payload: return
        async with aiohttp.ClientSession(headers=TakionConfig.HEADERS) as session:
            async with session.patch(TakionConfig.BASE_URL + f'/{takion.id}', json=payload) as resp:
                resp.raise_for_status()

    @asyncify
    def get_current_fixer(self, takion: TakionUser) -> DailyFixer:
        account_id = int(takion.account)
        for row in self._fixer_worksheet.get(value_render_option=gspread.utils.ValueRenderOption.unformatted):
            if FixerConfig.ACCOUNT_COL >= len(row): continue
            if row[FixerConfig.ACCOUNT_COL] == account_id:
                return DailyFixer(
                    takion=takion,
                    trigger=row[FixerConfig.TRIGGER_COL],
                    step=row[FixerConfig.STEP_COL]
                )
        raise KeyError(f'No such fixer sheet account: {account_id}')
    
    @asyncify
    def set_fixer(self, takion: TakionUser, trigger: int = None, step: int = None):
        cell = self._fixer_worksheet.find(takion.account)
        if not cell:
            raise KeyError(f'No such fixer sheet account: {takion.account}')
        if trigger:
            self._fixer_worksheet.update_cell(cell.row, FixerConfig.TRIGGER_COL + 1, trigger)
        if step:
            self._fixer_worksheet.update_cell(cell.row, FixerConfig.STEP_COL + 1, step)
    
manager = RiskManager()