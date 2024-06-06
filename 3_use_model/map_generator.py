import sys
import json
import folium
import pandas as pd
import joblib
import sqlite3
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import requests
import re

# args = '{"city":"Нижний Новгород","address":"Бориса Панина 1А","area":"63","year":"1977","floors":"5"}'
# data = json.loads(args)
# print(data)

print("Arguments received:", sys.argv)
# Load data from command line argument
data = json.loads(sys.argv[-1])


new_data = data

# Load additional resources
conn = sqlite3.connect("/Users/dima/Desktop/Диплом/Data/best_data.db")
query = "SELECT * FROM dataframe"
df = pd.read_sql_query(query, conn)
conn.close()
model = joblib.load('/Users/dima/Desktop/Диплом/Data/knn_model.pkl')
scaler = joblib.load('/Users/dima/Desktop/Диплом/Data/scaler.pkl')

# Process data to get coordinates
replacements = {
    'ул. ': '',
    'д.\xa0': '',
    '\xa0': ' ',
    'д.': '',
    ',': '',
    'б-р': 'бульвар',
    'просп.': 'проспект',
    'пер.': 'переулок',
    'пос.': 'посёлок',
    'ш.': 'шоссе',
    '  ': ' ',
    '-я': ''
}

val = new_data['address']
for old, new in replacements.items():
    val = val.replace(old, new)
regex_replacements = [
    (r'\bмкр\.\s*(\d+)-й\s*(\d+)\b', r'\1 микрорайон \2'),
    (r'\bмкр\.\s*([\w\s]+)\s*(\d+)-й\s*(\d+)\b', r'\2 микрорайон \1 \3')
]
if 'мкр.' in val:
    for pattern, repl in regex_replacements:
        val = re.sub(pattern, repl, val)
new_data['address'] = val

link = f"https://nominatim.openstreetmap.org/search.php?q={new_data['city'].replace(' ', '+')}+{new_data['address'].replace(' ', '+')}&format=jsonv2"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
response = requests.get(link, headers=headers)

if response.status_code == 200:
    data_json = response.json()
    if data_json:
        new_data['lat'] = data_json[0]['lat']
        new_data['lon'] = data_json[0]['lon']

# Prepare new data for prediction
edited_new_data = pd.DataFrame({
    'Широта': [new_data.get('lat')],
    'Долгота': [new_data.get('lon')],
    'Год постройки': [new_data.get('year')],
    'Этажность': [new_data.get('floors')],
    'Общая площадь': [new_data.get('area')]
})
new_data_scaled = scaler.transform(edited_new_data)
predicted_price = model.predict(new_data_scaled)

distances, indices = model.kneighbors(new_data_scaled)
neighbors = df.iloc[indices[0]]

qs = [0, 0.5, 0.75, 0.9, 0.99, 1]
quantiles = pd.qcut(df['Цена'], q=qs, labels=False)
colors_list = plt.get_cmap('plasma', 5)

m = folium.Map(location=[df['Широта'].mean(), df['Долгота'].mean()], zoom_start=12, tiles='CartoDB positron')

for idx, row in df.iterrows():
    quantile = quantiles[idx]
    color = colors.to_hex(colors_list(quantile))
    popup_info = f'''
    <b>Цена:</b> {row["Цена"]:,.0f}<br>
    <b>Широта:</b> {row["Широта"]:.4f}<br>
    <b>Долгота:</b> {row["Долгота"]:.4f}<br>
    <b>Год постройки:</b> {row["Год постройки"]:.0f}<br>
    <b>Этажность:</b> {row["Этажность"]:.0f}<br>
    <b>Общая площадь:</b> {row["Общая площадь"]:.0f}<br>
    '''
    popup_info = popup_info.replace(",", " ")
    folium.CircleMarker(
        location=[row['Широта'], row['Долгота']],
        radius=2,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_info, max_width=300)
    ).add_to(m)

# Добавление соседей на карту
for idx, row in neighbors.iterrows():
    popup_info = f'''
    <b>Цена:</b> {row["Цена"]:,.0f}<br>
    <b>Широта:</b> {row["Широта"]:.4f}<br>
    <b>Долгота:</b> {row["Долгота"]:.4f}<br>
    <b>Год постройки:</b> {row["Год постройки"]:.0f}<br>
    <b>Этажность:</b> {row["Этажность"]:.0f}<br>
    <b>Общая площадь:</b> {row["Общая площадь"]:.0f}<br>
    '''
    popup_info = popup_info.replace(",", " ")
    folium.CircleMarker(
        location=[row['Широта'], row['Долгота']],
        radius=5,
        color='green',
        fill=True,
        fill_color='lightgreen',
        fill_opacity=0.7,
        popup=folium.Popup(popup_info, max_width=300)
    ).add_to(m)

# Добавление нового объекта на карту
popup_info = f'''
<b>Предсказание:</b> {predicted_price[0]:,.0f}<br>
<b>Широта:</b> {edited_new_data["Широта"].values[0]}<br>
<b>Долгота:</b> {edited_new_data["Долгота"].values[0]}<br>
<b>Год постройки:</b> {edited_new_data["Год постройки"].values[0]}<br>
<b>Этажность:</b> {edited_new_data["Этажность"].values[0]}<br>
<b>Общая площадь:</b> {edited_new_data["Общая площадь"].values[0]}<br>
'''
popup_info = popup_info.replace(",", " ")

folium.Marker(
    location=[edited_new_data['Широта'].values[0], edited_new_data['Долгота'].values[0]],
    popup=folium.Popup(popup_info, max_width=300, show=True),
    icon=folium.Icon(color='green')
).add_to(m)

# Добавление легенды
colormap = folium.StepColormap(
    colors=[colors.to_hex(colors_list(i)) for i in range(5)],
    index=[df['Цена'].quantile(q) for q in qs],
    vmin=df['Цена'].min(), vmax=df['Цена'].max(),
    caption='Цена'
)
colormap.add_to(m)

# Saving the map to an HTML file with spaces replaced by pluses
city = data['city'].replace(" ", "+")
address = data['address'].replace(" ", "+")
area = data['area'].replace(" ", "+")
year = data['year'].replace(" ", "+")
floors = data['floors'].replace(" ", "+")

file_name = f'/Users/dima/Desktop/Диплом/Data/prediction-for-{city}-{address}-{area}-{year}-{floors}.html'
m.save(file_name)
