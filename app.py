import streamlit as st import pandas as pd from datetime import datetime

st.set_page_config(page_title="Value Bets", layout="wide")

Функция за определяне на сигурността на залога

def get_security_style(value_percent, odd, market): base_score = value_percent

if odd <= 1.8:
    base_score += 1.5
elif odd <= 2.2:
    base_score += 1
elif odd <= 3.0:
    base_score += 0.5
else:
    base_score -= 1

if market.lower() in ["1", "2", "1x", "x2", "двоен шанс"]:
    base_score += 1
elif market.lower() in ["над 2.5", "под 2.5", "гг", "без голове"]:
    base_score += 0.5
elif market.lower() in ["точен резултат", "хендикап", "първо полувреме"]:
    base_score -= 1

if base_score >= 9:
    return "Висока", "#bbf7d0"
elif base_score >= 6:
    return "Средна", "#fef9c3"
else:
    return "Ниска", "#f3f4f6"

Примерни прогнози

data = [ {"Мач": "Ливърпул - Манчестър Юнайтед", "Час": "19:30", "Пазар": "1", "Коефициент": 1.95, "Value %": 8.5}, {"Мач": "Барселона - Реал Мадрид", "Час": "22:00", "Пазар": "над 2.5", "Коефициент": 2.10, "Value %": 7.2}, {"Мач": "Байерн - Борусия Д", "Час": "21:30", "Пазар": "ГГ", "Коефициент": 1.80, "Value %": 6.0}, {"Мач": "Ювентус - Интер", "Час": "21:45", "Пазар": "1X", "Коефициент": 1.65, "Value %": 9.3}, {"Мач": "Арсенал - Челси", "Час": "20:00", "Пазар": "точен резултат", "Коефициент": 6.50, "Value %": 12.0} ] df = pd.DataFrame(data)

st.title("Прогнози за днес")

for i, row in df.iterrows(): security_label, bg_color = get_security_style(row["Value %"], row["Коефициент"], row["Пазар"])

with st.container(border=True):
    st.markdown(
        f'<div style="background-color:{bg_color}; padding:15px; border-radius:12px; margin-bottom:10px;">
        <h4 style="margin:0;">{row["Мач"]}</h4>
        <p style="margin:0;">Час: {row["Час"]} | Пазар: <strong>{row["Пазар"]}</strong> | Коеф.: {row["Коефициент"]} | Value: {row["Value %"]}%</p>
        <p style="margin:0; font-weight:bold;">Сигурност: {security_label}</p>
        </div>',
        unsafe_allow_html=True
    )

