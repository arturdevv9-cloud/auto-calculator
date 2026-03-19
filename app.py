import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# -------------------- Конфигурация страницы --------------------
st.set_page_config(
    page_title="Автокалькулятор с ручным вводом курсов",
    page_icon="🚗",
    layout="wide"
)

# -------------------- Заголовок --------------------
st.title("🚗 Калькулятор стоимости автомобиля с таможенными платежами")
st.markdown("Актуальные ставки утильсбора: **декабрь 2025 — 2026 год**")
st.markdown("---")

# -------------------- Конвертер мощности --------------------
def hp_to_kw(hp):
    return hp * 0.7355

def kw_to_hp(kw):
    return kw / 0.7355

# -------------------- Класс калькулятора таможенных платежей --------------------
class CustomsCalculator:
    def __init__(self, rates):
        self.rates = rates  # словарь {код_валюты: курс_руб}
        self.base_rate = 20000
    
    def convert_to_rub(self, amount, currency):
        if currency == 'RUB':
            return amount
        rate = self.rates.get(currency)
        if rate is None:
            raise ValueError(f"Нет курса для валюты {currency}")
        return amount * rate
    
    def calculate_duty(self, cost_rub, engine_volume, car_age, is_individual=True):
        eur_rate = self.rates.get('EUR')
        if eur_rate is None:
            raise ValueError("Нет курса евро для расчёта пошлины")
        
        if not is_individual:
            if car_age <= 7:
                duty = cost_rub * 0.54
                method = "54% от стоимости (юрлицо, <=7 лет)"
                rate_eur = None
            else:
                if engine_volume <= 1000:
                    rate_eur = 1.5
                elif engine_volume <= 1500:
                    rate_eur = 1.7
                elif engine_volume <= 1800:
                    rate_eur = 2.5
                elif engine_volume <= 2300:
                    rate_eur = 2.7
                elif engine_volume <= 3000:
                    rate_eur = 3.0
                else:
                    rate_eur = 3.6
                duty = engine_volume * rate_eur * eur_rate
                method = f"{rate_eur}€/см³ (юрлицо, >7 лет)"
            return {
                'duty': duty,
                'method': method,
                'rate_eur': rate_eur,
                'used_volume': engine_volume,
                'eur_rate': eur_rate
            }
        
        # Для физических лиц
        if car_age <= 3:
            duty1 = cost_rub * 0.54
            duty2 = engine_volume * 2.5 * eur_rate
            duty = max(duty1, duty2)
            method = "max(54% от стоимости, 2.5€/см³)"
            rate_eur = 2.5
        elif 3 < car_age <= 5:
            if engine_volume <= 1000:
                rate_eur = 1.5
            elif engine_volume <= 1500:
                rate_eur = 1.7
            elif engine_volume <= 1800:
                rate_eur = 2.5
            elif engine_volume <= 2300:
                rate_eur = 2.7
            elif engine_volume <= 3000:
                rate_eur = 3.0
            else:
                rate_eur = 3.6
            duty = engine_volume * rate_eur * eur_rate
            method = f"{rate_eur}€/см³ (3-5 лет)"
        else:
            # Старше 5 лет (включая 5-7 и >7)
            if engine_volume <= 1000:
                rate_eur = 3.0
            elif engine_volume <= 1500:
                rate_eur = 3.2
            elif engine_volume <= 1800:
                rate_eur = 3.5
            elif engine_volume <= 2300:
                rate_eur = 4.8
            elif engine_volume <= 3000:
                rate_eur = 5.0
            else:
                rate_eur = 5.7
            duty = engine_volume * rate_eur * eur_rate
            method = f"{rate_eur}€/см³ (>5 лет)"
        
        return {
            'duty': duty,
            'method': method,
            'rate_eur': rate_eur,
            'used_volume': engine_volume,
            'eur_rate': eur_rate
        }
    
    def calculate_util(self, engine_volume, power_hp, car_age, is_electric, is_individual=True):
        power_kw = hp_to_kw(power_hp)
        
        if is_individual and power_hp <= 160 and (is_electric or engine_volume <= 3000):
            if car_age <= 3:
                return 3400
            else:
                return 5200
        
        if is_electric or engine_volume == 0:
            return self._util_electric(power_kw, car_age)
        elif engine_volume <= 2000:
            return self._util_small_engine(engine_volume, power_kw, car_age)
        elif engine_volume <= 3000:
            return self._util_medium_engine(engine_volume, power_kw, car_age)
        else:
            return self._util_large_engine(engine_volume, car_age)
    
    def _util_electric(self, power_kw, car_age):
        if car_age <= 3:
            if power_kw <= 58.85:
                return 20000 * 0.17
            elif power_kw <= 73.55:
                return 20000 * 49.56
            elif power_kw <= 95.61:
                return 20000 * 65.88
            elif power_kw <= 117.68:
                return 20000 * 78.00
            elif power_kw <= 139.75:
                return 20000 * 92.40
            elif power_kw <= 161.81:
                return 20000 * 109.68
            elif power_kw <= 183.88:
                return 20000 * 129.96
            elif power_kw <= 205.94:
                return 20000 * 153.96
            else:
                return 20000 * 182.40
        else:
            if power_kw <= 58.85:
                return 20000 * 0.26
            elif power_kw <= 73.55:
                return 20000 * 82.08
            elif power_kw <= 95.61:
                return 20000 * 95.64
            elif power_kw <= 117.68:
                return 20000 * 111.36
            elif power_kw <= 139.75:
                return 20000 * 129.72
            elif power_kw <= 161.81:
                return 20000 * 151.20
            elif power_kw <= 183.88:
                return 20000 * 176.16
            elif power_kw <= 205.94:
                return 20000 * 205.20
            else:
                return 20000 * 239.04
    
    def _util_small_engine(self, engine_volume, power_kw, car_age):
        if car_age <= 3:
            if power_kw <= 117.68:
                return 20000 * 0.17
            elif power_kw <= 139.75:
                return 20000 * 45.00
            elif power_kw <= 161.81:
                return 20000 * 47.64
            elif power_kw <= 183.88:
                return 20000 * 50.52
            elif power_kw <= 205.94:
                return 20000 * 57.12
            elif power_kw <= 228:
                return 20000 * 64.56
            elif power_kw <= 250:
                return 20000 * 72.96
            elif power_kw <= 272.13:
                return 20000 * 83.16
            elif power_kw <= 294.2:
                return 20000 * 94.80
            elif power_kw <= 316.26:
                return 20000 * 108.00
            elif power_kw <= 338.33:
                return 20000 * 123.24
            elif power_kw <= 367.75:
                return 20000 * 140.40
            else:
                return 20000 * 160.08
        else:
            if power_kw <= 117.68:
                return 20000 * 0.26
            elif power_kw <= 139.75:
                return 20000 * 74.64
            elif power_kw <= 161.81:
                return 20000 * 79.20
            elif power_kw <= 183.88:
                return 20000 * 83.88
            elif power_kw <= 205.94:
                return 20000 * 91.92
            elif power_kw <= 228:
                return 20000 * 100.56
            elif power_kw <= 250:
                return 20000 * 110.16
            elif power_kw <= 272.13:
                return 20000 * 120.60
            elif power_kw <= 294.2:
                return 20000 * 132.00
            elif power_kw <= 316.26:
                return 20000 * 144.60
            elif power_kw <= 338.33:
                return 20000 * 158.40
            elif power_kw <= 367.75:
                return 20000 * 173.40
            else:
                return 20000 * 189.84
    
    def _util_medium_engine(self, engine_volume, power_kw, car_age):
        if car_age <= 3:
            if power_kw <= 117.68:
                return 20000 * 0.17
            elif power_kw <= 139.75:
                return 20000 * 115.34
            elif power_kw <= 161.81:
                return 20000 * 118.20
            elif power_kw <= 183.88:
                return 20000 * 120.12
            elif power_kw <= 205.94:
                return 20000 * 126.00
            elif power_kw <= 228:
                return 20000 * 131.04
            elif power_kw <= 250:
                return 20000 * 136.32
            elif power_kw <= 272.13:
                return 20000 * 141.72
            elif power_kw <= 294.2:
                return 20000 * 147.48
            elif power_kw <= 316.26:
                return 20000 * 153.36
            elif power_kw <= 338.33:
                return 20000 * 159.48
            elif power_kw <= 367.75:
                return 20000 * 165.84
            else:
                return 20000 * 172.44
        else:
            if power_kw <= 117.68:
                return 20000 * 0.26
            elif power_kw <= 139.75:
                return 20000 * 172.80
            elif power_kw <= 161.81:
                return 20000 * 175.08
            elif power_kw <= 183.88:
                return 20000 * 177.60
            elif power_kw <= 205.94:
                return 20000 * 183.00
            elif power_kw <= 228:
                return 20000 * 188.52
            elif power_kw <= 250:
                return 20000 * 193.68
            elif power_kw <= 272.13:
                return 20000 * 199.08
            elif power_kw <= 294.2:
                return 20000 * 204.72
            elif power_kw <= 316.26:
                return 20000 * 210.48
            elif power_kw <= 338.33:
                return 20000 * 216.36
            elif power_kw <= 367.75:
                return 20000 * 222.36
            else:
                return 20000 * 228.60
    
    def _util_large_engine(self, engine_volume, car_age):
        if car_age <= 3:
            if engine_volume <= 3500:
                return 20000 * 107.50
            else:
                return 20000 * 137.00
        else:
            if engine_volume <= 3500:
                return 20000 * 165.00
            else:
                return 20000 * 180.00
    
    def calculate_customs_fee(self, cost_rub):
        if cost_rub <= 200000:
            return 775
        elif cost_rub <= 450000:
            return 1550
        elif cost_rub <= 1200000:
            return 3100
        elif cost_rub <= 2700000:
            return 8530
        elif cost_rub <= 4200000:
            return 12000
        elif cost_rub <= 5500000:
            return 15500
        elif cost_rub <= 7000000:
            return 20000
        elif cost_rub <= 8000000:
            return 23000
        elif cost_rub <= 9000000:
            return 25000
        elif cost_rub <= 10000000:
            return 27000
        else:
            return 30000
    
    def calculate_total(self, car_data):
        cost_rub = self.convert_to_rub(car_data['cost'], car_data['currency'])
        
        if car_data.get('manual_duty', 0) > 0:
            duty = car_data['manual_duty']
            duty_info = {'duty': duty, 'method': 'введено вручную', 'rate_eur': None, 'used_volume': None, 'eur_rate': None}
        else:
            duty_info = self.calculate_duty(
                cost_rub,
                car_data['engine_volume'],
                car_data['car_age'],
                car_data.get('is_individual', True)
            )
            duty = duty_info['duty']
        
        if car_data.get('manual_util', 0) > 0:
            util = car_data['manual_util']
        else:
            util = self.calculate_util(
                car_data['engine_volume'],
                car_data['power_hp'],
                car_data['car_age'],
                car_data['is_electric'],
                car_data.get('is_individual', True)
            )
        
        customs_fee = self.calculate_customs_fee(cost_rub)
        total_payments = duty + util + customs_fee
        
        bank_commission = 0
        if car_data.get('use_vtb_commission'):
            bank_commission = cost_rub * 0.025
        
        broker_fee = car_data.get('broker_fee', 0)
        additional = car_data.get('additional_costs', 0)
        
        interest_rate = car_data.get('interest_rate', 0)
        if interest_rate > 0:
            interest = (cost_rub + total_payments + bank_commission + broker_fee + additional) * interest_rate / 100
        else:
            interest = 0
        
        total_with_all = cost_rub + total_payments + bank_commission + broker_fee + additional + interest
        
        return {
            'currency': car_data['currency'],
            'exchange_rate': self.rates.get(car_data['currency'], 1),
            'cost_rub': cost_rub,
            'duty': duty,
            'duty_info': duty_info,
            'util': util,
            'customs_fee': customs_fee,
            'total_payments': total_payments,
            'bank_commission': bank_commission,
            'broker_fee': broker_fee,
            'additional_costs': additional,
            'interest_rate': interest_rate,
            'interest': interest,
            'total_with_all': total_with_all
        }

# -------------------- Инициализация сессии --------------------
if 'rates' not in st.session_state:
    st.session_state.rates = {}  # словарь для хранения вручную введённых курсов
if 'saved_calcs' not in st.session_state:
    st.session_state.saved_calcs = []

# -------------------- Боковая панель --------------------
with st.sidebar:
    st.header("📊 Ручной ввод курсов валют")
    st.markdown("Введите курсы для необходимых валют (RUB вводить не нужно).")
    
    # Список основных валют
    main_currencies = ['USD', 'EUR', 'CNY', 'JPY', 'KRW']
    
    # Отображение уже введённых курсов
    if st.session_state.rates:
        rates_data = []
        for curr, rate in st.session_state.rates.items():
            rates_data.append({"Валюта": curr, "Курс (₽)": f"{rate:.2f}"})
        st.dataframe(pd.DataFrame(rates_data), hide_index=True, use_container_width=True)
    else:
        st.info("Пока не введено ни одного курса.")
    
    st.markdown("---")
    st.subheader("✏️ Добавить / изменить курс")
    
    # Выбор валюты
    currency_options = main_currencies + [c for c in st.session_state.rates.keys() if c not in main_currencies]
    selected_currency = st.selectbox("Валюта", options=currency_options, key="manual_currency_select")
    
    # Текущее значение (если есть)
    current_val = st.session_state.rates.get(selected_currency, 0.0)
    new_rate = st.number_input(
        f"Курс {selected_currency} (₽)",
        min_value=0.0,
        value=current_val if current_val > 0 else 0.0,
        step=0.01,
        format="%.2f",
        key="manual_rate_input"
    )
    
    if st.button("Сохранить курс"):
        if new_rate > 0:
            st.session_state.rates[selected_currency] = new_rate
            st.success(f"Курс {selected_currency} = {new_rate} ₽ сохранён")
            # Автоматически выбираем эту валюту в основном селекте
            st.session_state['currency_selector'] = selected_currency
            st.rerun()
        else:
            st.error("Введите корректный курс больше 0")
    
    st.markdown("---")
    st.subheader("⚙️ Ручная корректировка платежей")
    manual_duty = 0.0
    manual_util = 0.0
    use_manual_duty = st.checkbox("Ввести пошлину вручную")
    if use_manual_duty:
        manual_duty = st.number_input("Пошлина (₽)", min_value=0.0, step=1000.0, key="manual_duty")
    use_manual_util = st.checkbox("Ввести утильсбор вручную")
    if use_manual_util:
        manual_util = st.number_input("Утильсбор (₽)", min_value=0.0, step=1000.0, key="manual_util")
    
    st.markdown("---")
    st.subheader("💾 Сохраненные расчеты")
    if st.session_state.saved_calcs:
        saved_options = [f"{i+1}. {entry['timestamp']}" for i, entry in enumerate(st.session_state.saved_calcs)]
        selected_idx = st.selectbox("Выберите расчет", range(len(saved_options)), format_func=lambda x: saved_options[x])
        if st.button("Показать сохраненный расчет"):
            entry = st.session_state.saved_calcs[selected_idx]
            st.write("**Входные данные:**")
            st.json(entry['car_data'])
            st.write("**Результаты:**")
            res = entry['result']
            col1, col2, col3 = st.columns(3)
            col1.metric("Стоимость авто (руб)", f"{res['cost_rub']:,.0f} ₽")
            col2.metric("Таможенные платежи", f"{res['total_payments']:,.0f} ₽")
            col3.metric("Полная стоимость", f"{res['total_with_all']:,.0f} ₽")
    else:
        st.info("Нет сохраненных расчетов")
    
    st.markdown("---")
    st.markdown("### О калькуляторе")
    st.markdown("""
    Учтены изменения 2026 года:
    - Утильсбор зависит от мощности и объёма
    - Льгота до 160 л.с. и объёма ≤3 л (только для физлиц)
    - Для электромобилей – особая шкала
    - Курсы вводятся вручную
    - Добавлена комиссия ВТБ (2.5%) и услуги брокера
    - Сохранение расчетов
    """)

# -------------------- Основная форма ввода --------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Данные автомобиля")
    cost = st.number_input("Стоимость автомобиля", min_value=1000.0, value=20000.0, step=1000.0)
    
    # Доступные валюты: RUB + все, для которых есть курс в st.session_state.rates
    available_currencies = ['RUB'] + list(st.session_state.rates.keys())
    # Убираем дубликаты, если RUB уже есть в rates
    available_currencies = list(dict.fromkeys(available_currencies))
    
    # Индекс для выбора: если есть сохранённая валюта, ставим её, иначе 0
    default_index = 0
    saved_currency = st.session_state.get('currency_selector', None)
    if saved_currency and saved_currency in available_currencies:
        default_index = available_currencies.index(saved_currency)
    
    currency = st.selectbox(
        "Валюта",
        options=available_currencies,
        index=default_index,
        key="currency_selector"
    )
    
    engine_type = st.radio("Тип двигателя", ["ДВС", "Электромобиль/Гибрид"], horizontal=True)
    is_electric = (engine_type == "Электромобиль/Гибрид")
    
    if not is_electric:
        engine_volume = st.number_input("Объём двигателя (см³)", min_value=500, max_value=8000, value=2000, step=100)
    else:
        engine_volume = 0
        st.info("Для электромобилей объём не учитывается")
    
    power_unit = st.radio("Единица мощности", ["л.с.", "кВт"], horizontal=True, key="power_unit")
    if power_unit == "л.с.":
        power_hp = st.number_input("Мощность (л.с.)", min_value=50, max_value=1000, value=150, step=10)
        st.caption(f"≈ {hp_to_kw(power_hp):.1f} кВт")
    else:
        power_kw = st.number_input("Мощность (кВт)", min_value=40, max_value=750, value=110, step=5)
        power_hp = kw_to_hp(power_kw)
        st.caption(f"≈ {power_hp:.0f} л.с.")
    
    # Возрастные категории
    age_category = st.radio(
        "Возраст авто",
        options=["до 3 лет", "3-5 лет", "5-7 лет", "более 7 лет"],
        horizontal=True,
        index=0
    )
    if age_category == "до 3 лет":
        car_age = 2
    elif age_category == "3-5 лет":
        car_age = 4
    elif age_category == "5-7 лет":
        car_age = 6
    else:
        car_age = 10
    
    vehicle_type = st.selectbox("Тип транспортного средства", 
                                ["Легковой автомобиль", "Мотоцикл", "Грузовой автомобиль", "Автобус"], 
                                index=0, key="vehicle_type")

with col2:
    st.subheader("💰 Дополнительные параметры")
    
    use_vtb_commission = st.checkbox("Учитывать комиссию банка ВТБ (2.5% от стоимости авто)")
    
    broker_fee = st.number_input(
        "Услуги брокера (₽)",
        min_value=0.0,
        value=0.0,
        step=1000.0,
        help="Введите стоимость услуг брокера вручную"
    )
    
    additional_costs = st.number_input(
        "Дополнительные расходы (₽)",
        min_value=0.0,
        value=0.0,
        step=1000.0,
        help="Доставка, страховка и т.п."
    )
    
    use_interest = st.checkbox("Учитывать кредит")
    interest_rate = 0.0
    if use_interest:
        interest_rate = st.number_input("Процентная ставка (%)", 0.0, 50.0, 15.0, 0.5)
    
    import_purpose = st.radio("Цель ввоза", 
                              ["Для личного пользования (физлицо)", "Для коммерческих целей (юрлицо)"], 
                              horizontal=True, key="import_purpose")
    is_individual = (import_purpose == "Для личного пользования (физлицо)")
    
    # Информация о льготах
    if is_individual and power_hp <= 160 and (is_electric or engine_volume <= 3000):
        st.success("✅ Автомобиль подпадает под льготную ставку утильсбора")
    else:
        reasons = []
        if not is_individual:
            reasons.append("цель ввоза - коммерческая")
        if power_hp > 160:
            reasons.append(f"мощность {power_hp:.0f} л.с. > 160")
        if not is_electric and engine_volume > 3000:
            reasons.append(f"объём {engine_volume} см³ > 3000")
        st.warning(f"⚠️ Льгота не применяется: {', '.join(reasons)}")

# Кнопка расчёта
if st.button("🧮 Рассчитать полную стоимость", type="primary", use_container_width=True):
    # Проверка наличия курса для выбранной валюты (если это не RUB)
    if currency != 'RUB' and currency not in st.session_state.rates:
        st.error(f"Нет курса для валюты {currency}. Введите его в боковой панели.")
        st.stop()
    
    if vehicle_type != "Легковой автомобиль":
        st.warning("Калькулятор в текущей версии поддерживает только легковые автомобили.")
        st.stop()
    
    car_data = {
        'cost': cost,
        'currency': currency,
        'engine_volume': engine_volume,
        'car_age': car_age,
        'power_hp': power_hp,
        'is_electric': is_electric,
        'use_vtb_commission': use_vtb_commission,
        'broker_fee': broker_fee,
        'interest_rate': interest_rate if use_interest else 0,
        'additional_costs': additional_costs,
        'manual_duty': manual_duty if use_manual_duty else 0,
        'manual_util': manual_util if use_manual_util else 0,
        'is_individual': is_individual,
        'vehicle_type': vehicle_type
    }
    
    calc = CustomsCalculator(st.session_state.rates)
    
    try:
        result = calc.calculate_total(car_data)
        
        st.markdown("---")
        st.subheader("📊 Результаты расчёта")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Стоимость авто (руб)", f"{result['cost_rub']:,.0f} ₽")
        col2.metric("Таможенные платежи", f"{result['total_payments']:,.0f} ₽")
        col3.metric("Полная стоимость", f"{result['total_with_all']:,.0f} ₽")
        
        duty_info = result['duty_info']
        if duty_info['method'] != 'введено вручную':
            st.markdown(f"**Детали пошлины:** {duty_info['method']}")
            if duty_info['rate_eur']:
                st.markdown(f"- Ставка: {duty_info['rate_eur']} €/см³")
            if duty_info['used_volume']:
                st.markdown(f"- Объём двигателя: {duty_info['used_volume']} см³")
            st.markdown(f"- Курс евро: {duty_info['eur_rate']:.2f} ₽")
        
        st.markdown("### Детализация расходов")
        
        details = {
            'Показатель': [
                'Стоимость авто (исходная)',
                f'Курс {currency}/руб',
                'Стоимость авто (руб)',
                'Таможенные платежи (пошлина + утильсбор + сбор)',
            ],
            'Сумма': [
                f"{cost:,.0f} {currency}",
                f"{result['exchange_rate']:.2f}",
                f"{result['cost_rub']:,.0f} ₽",
                f"{result['total_payments']:,.0f} ₽"
            ]
        }
        
        if result['bank_commission'] > 0:
            details['Показатель'].append('Комиссия банка ВТБ (2.5%)')
            details['Сумма'].append(f"{result['bank_commission']:,.0f} ₽")
        
        if result['broker_fee'] > 0:
            details['Показатель'].append('Услуги брокера')
            details['Сумма'].append(f"{result['broker_fee']:,.0f} ₽")
        
        if result['additional_costs'] > 0:
            details['Показатель'].append('Дополнительные расходы')
            details['Сумма'].append(f"{result['additional_costs']:,.0f} ₽")
        
        if result['interest'] > 0:
            details['Показатель'].append(f'Проценты по кредиту ({interest_rate}%)')
            details['Сумма'].append(f"{result['interest']:,.0f} ₽")
        
        details['Показатель'].append('ПОЛНАЯ СТОИМОСТЬ')
        details['Сумма'].append(f"{result['total_with_all']:,.0f} ₽")
        
        st.dataframe(pd.DataFrame(details), hide_index=True, use_container_width=True)
        
        st.markdown("### Структура расходов")
        
        labels = ['Стоимость авто', 'Таможенные платежи']
        values = [result['cost_rub'], result['total_payments']]
        
        if result['bank_commission'] > 0:
            labels.append('Комиссия банка')
            values.append(result['bank_commission'])
        if result['broker_fee'] > 0:
            labels.append('Брокер')
            values.append(result['broker_fee'])
        if result['additional_costs'] > 0:
            labels.append('Доп. расходы')
            values.append(result['additional_costs'])
        if result['interest'] > 0:
            labels.append('Проценты')
            values.append(result['interest'])
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            textinfo='label+percent',
            marker=dict(colors=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A4E7A', '#1E7640'])
        )])
        fig.update_layout(title="Распределение общей стоимости")
        st.plotly_chart(fig, use_container_width=True)
        
        if st.button("💾 Сохранить расчет", key="save_calc"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            saved_entry = {
                'timestamp': timestamp,
                'car_data': car_data.copy(),
                'result': result.copy()
            }
            st.session_state.saved_calcs.append(saved_entry)
            st.success(f"Расчет сохранен под меткой {timestamp}")
            st.rerun()
        
    except Exception as e:
        st.error(f"Ошибка при расчёте: {e}")
        st.exception(e)
        
