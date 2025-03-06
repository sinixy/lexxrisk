import aiohttp
import gspread
import gspread.utils
from dataclasses import dataclass

from config import TakionConfig, GSKEY_PATH, RiskConfig, FixerConfig
from common.utils import asyncify


@dataclass
class DailyRisk:
    name: str
    account: int
    stop: int
    cover: int

@dataclass
class DailyFixer:
    account: int
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

    @asyncify
    def get_max_risk(self, account_id: int) -> DailyRisk:
        for row in self._risk_worksheet.get(value_render_option=gspread.utils.ValueRenderOption.unformatted):
            if RiskConfig.ACCOUNT_COL >= len(row): continue
            if row[RiskConfig.ACCOUNT_COL] == account_id:
                return DailyRisk(
                    name=row[RiskConfig.NAME_COL],
                    account=row[RiskConfig.ACCOUNT_COL],
                    stop=row[RiskConfig.STOP_COL],
                    cover=row[RiskConfig.COVER_COL]
                )
        raise KeyError(f'No such account: {account_id}')
    
    async def get_current_risk(self, account_id: int) -> DailyRisk:
        return await self.get_max_risk(account_id)
    
        async with aiohttp.ClientSession(headers=TakionConfig.HEADERS) as session:
            async with session.get(TakionConfig.BASE_URL + f'/{account_id}') as resp:
                resp.raise_for_status()
                data = await resp.json()
                return DailyRisk(
                    name=data['user']['first_name']+data['user']['last_name'],
                    account=account_id,
                    stop=data['max_loss'],
                    cover=data['max_loss_close']
                )

    async def set_stop(self, account_id: int, stop: int):
        await self.set_risk(account_id, stop=stop)

    async def set_cover(self, account_id: int, cover: int):
        await self.set_risk(account_id, cover=cover)

    async def set_risk(self, account_id: int, stop: int = None, cover: int = None):
        return
    
        payload = {}
        if stop: payload['max_loss'] = stop
        if cover: payload['max_loss_close'] = cover
        if not payload: return
        async with aiohttp.ClientSession(headers=TakionConfig.HEADERS) as session:
            async with session.patch(TakionConfig.BASE_URL + f'/{account_id}') as resp:
                resp.raise_for_status()

    @asyncify
    def get_current_fixer(self, account_id: int) -> DailyFixer:
        for row in self._fixer_worksheet.get(value_render_option=gspread.utils.ValueRenderOption.unformatted):
            if FixerConfig.ACCOUNT_COL >= len(row): continue
            if row[FixerConfig.ACCOUNT_COL] == account_id:
                return DailyFixer(
                    account=row[FixerConfig.ACCOUNT_COL],
                    trigger=row[FixerConfig.TRIGGER_COL],
                    step=row[FixerConfig.STEP_COL]
                )
        raise KeyError(f'No such account: {account_id}')
    
    @asyncify
    def set_fixer(self, account_id: int, trigger: int = None, step: int = None):
        cell = self._fixer_worksheet.find(str(account_id))
        if not cell: raise KeyError(f'No such account: {account_id}')

        if trigger:
            self._fixer_worksheet.update_cell(cell.row, FixerConfig.TRIGGER_COL + 1, trigger)
        if step:
            self._fixer_worksheet.update_cell(cell.row, FixerConfig.STEP_COL + 1, step)
    
manager = RiskManager()