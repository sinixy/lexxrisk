from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from bot.models import User
from bot.keyboards.user import risk_menu, yes_no_kb, cancel_kb
from common.logger import logger
from risk import manager, TakionUser


router = Router(name='user')

class Stop(StatesGroup):
    input = State()
    confirm = State()

class Cover(StatesGroup):
    input = State()
    confirm = State()

class Fixer(StatesGroup):
    trigger = State()
    step = State()
    confirm = State()


@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext, user: User):
    await state.clear()
    welcome = f"Добро пожаловать, {user.name}!\n\n" if user.name else "Добро пожаловать!\n\n"
    welcome += f"Номер аккаунта: {user.account_id}"
    await message.answer(welcome, reply_markup=risk_menu)

@router.message(F.text == "Текущие условия")
async def current_risk(message: types.Message, takion: TakionUser):
    risk = await manager.get_current_risk(takion)
    await message.answer(f"Ваши условия:\n\nСтоп: {risk.stop}\nКавер: {risk.cover}")

@router.message(F.text == "Изменить стоп")
async def change_stop(message: types.Message, takion: TakionUser, state: FSMContext):
    risk = await manager.get_current_risk(takion)
    await message.answer(f"Текущий стоп: {risk.stop}\n\nВведите новый стоп:", reply_markup=cancel_kb)
    await state.set_state(Stop.input)

@router.message(F.text == "Изменить кавер")
async def change_cover(message: types.Message, takion: TakionUser, state: FSMContext):
    risk = await manager.get_current_risk(takion)
    await message.answer(f"Текущий кавер: {risk.cover}\n\nВведите новый кавер:", reply_markup=cancel_kb)
    await state.set_state(Cover.input)

@router.message(F.text == "Изменить фиксер")
async def change_fixer(message: types.Message, takion: TakionUser, state: FSMContext):
    fixer = await manager.get_current_fixer(takion)
    await message.answer(f"Текущий триггер: ${fixer.trigger}\nТекущий шаг: ${fixer.step}\n\nВведите новый триггер:", reply_markup=cancel_kb)
    await state.set_state(Fixer.trigger)

@router.message(Fixer.trigger, F.text)
async def change_fixer_trigger(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Некорректное значение! Попробуйте ещё раз:", reply_markup=cancel_kb)
        return
    trigger = int(message.text)
    if trigger < 0:
        await message.answer("Некорректное значение! Попробуйте ещё раз:", reply_markup=cancel_kb)
        return
    await state.update_data(trigger=trigger)
    await message.answer("Введите новый шаг:", reply_markup=cancel_kb)
    await state.set_state(Fixer.step)

@router.message(Fixer.step, F.text)
async def change_fixer_step(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Некорректное значение! Попробуйте ещё раз:", reply_markup=cancel_kb)
        return
    step = int(message.text)
    if step < 0:
        await message.answer("Некорректное значение! Попробуйте ещё раз:", reply_markup=cancel_kb)
        return
    await state.update_data(step=step)
    data = await state.get_data()
    await message.answer(f"Вы уверены, что хотите изменить триггер на ${data['trigger']} и шаг на ${data['step']}?", reply_markup=yes_no_kb)
    await state.set_state(Fixer.confirm)

@router.callback_query(Fixer.confirm, F.data == "yes")
async def confirm_fixer_change(callback: types.CallbackQuery, user: User, takion: TakionUser, state: FSMContext):
    data = await state.get_data()
    trigger, step = data['trigger'], data['step']
    logger.info(f"User(tg={user.tg_id}, takion={user.account_id}) requested to change fixer to trigger={trigger} and steap={step}")
    await manager.set_fixer(takion, trigger, step)
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Фиксер успешно установлен!")

def is_invalid_risk_val(val: int, max_val: int, current_val: int) -> str:
    if val > max_val:
        return f"Превышено максимальное значение - ${max_val}! Попробуйте ещё раз:"
    elif val == current_val:
        return "У вас уже выставлено это значение! Попробуйте ещё раз:"
    return ""

@router.message(Cover.input, F.text)
@router.message(Stop.input, F.text)
async def change_risk_val(message: types.Message, takion: TakionUser, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Некорректное значение! Попробуйте ещё раз:", reply_markup=cancel_kb)
        return
    new_val = int(message.text)
    if new_val <= 0:
        await message.answer("Некорректное значение! Попробуйте ещё раз:", reply_markup=cancel_kb)
        return

    max_risk = await manager.get_max_risk(takion)
    current_risk = await manager.get_current_risk(takion)
    state_name = await state.get_state()
    if state_name == Stop.input.state:
        if reason := is_invalid_risk_val(new_val, max_risk.stop, current_risk.stop):
            await message.answer(reason, reply_markup=cancel_kb)
            return
        text = f"Вы уверены, что хотите изменить стоп с ${current_risk.stop} на ${new_val}?"
        await state.set_data({"stop": new_val})
        await state.set_state(Stop.confirm)
    elif state_name == Cover.input.state:
        if reason := is_invalid_risk_val(new_val, max_risk.cover, current_risk.cover):
            await message.answer(reason)
            return
        text = f"Вы уверены, что хотите изменить кавер с ${current_risk.stop} на ${new_val}?"
        await state.set_data({"cover": new_val})
        await state.set_state(Cover.confirm)

    await message.answer(text, reply_markup=yes_no_kb)

@router.callback_query(Cover.confirm, F.data == "yes")
@router.callback_query(Stop.confirm, F.data == "yes")
async def confirm_risk_change(callback: types.CallbackQuery, user: User, takion: TakionUser, state: FSMContext):
    data = await state.get_data()

    state_name = await state.get_state()
    if state_name == Stop.confirm.state:
        logger.info(f"User(tg={user.tg_id}, takion={user.account_id}) requested to change stop to {data['stop']}")
        await manager.set_stop(takion, data['stop'])
    elif state_name == Cover.confirm.state:
        logger.info(f"User(tg={user.tg_id}, takion={user.account_id}) requested to change cover to {data['cover']}")
        await manager.set_cover(takion, data['cover'])
    
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Запрос на изменение риска отправлен!")
    

@router.callback_query(F.data == "cancel")
@router.callback_query(Cover.confirm, F.data == "no")
@router.callback_query(Stop.confirm, F.data == "no")
@router.callback_query(Fixer.confirm, F.data == "no")
async def cancel_change(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Изменения отменены.")
    await callback.message.delete()
