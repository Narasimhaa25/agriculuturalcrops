from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
from io import BytesIO
matplotlib.use('Agg')

app = Flask(__name__)

CSV_PATH = 'India_Agriculture.csv'
CHARTS_DIR = 'static/charts'
os.makedirs(CHARTS_DIR, exist_ok=True)

@app.route('/')
def home():
    return render_template('HomePage.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/data-entry', methods=['GET', 'POST'])
def data_entry():
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    df.dropna(subset=['State', 'District', 'Crop', 'Season'], inplace=True)
    columns = df.columns.tolist()
    states = sorted(df['State'].unique())
    crops = sorted(df['Crop'].unique())
    seasons = sorted(df['Season'].unique())
    districts_by_state = df.groupby('State')['District'].unique().apply(list).to_dict()

    if request.method == 'POST':
        new_row = {col: request.form.get(col, '').strip() for col in columns}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(CSV_PATH, index=False)
        return redirect(url_for('airecomm'))  # 🔁 Redirect to AI recommendation page

    return render_template(
        'data_entry.html',
        columns=columns,
        states=states,
        crops=crops,
        seasons=seasons,
        districts_by_state=districts_by_state
    )

@app.route('/visualization', methods=['GET', 'POST'])
def visualization():
    df = pd.read_csv(CSV_PATH, low_memory=False)
    df.columns = df.columns.str.strip()
    df['Area'] = pd.to_numeric(df['Area'], errors='coerce')
    df['Production'] = pd.to_numeric(df['Production'], errors='coerce')
    df.dropna(subset=['State', 'Crop_Year', 'Season', 'Production'], inplace=True)

    states = sorted(df['State'].unique())
    seasons = sorted(df['Season'].unique())
    years = sorted(df['Crop_Year'].unique())

    selected_state = request.form.get('state') or states[0]
    selected_season = request.form.get('season') or seasons[0]
    selected_year = int(request.form.get('year') or years[0])

    filtered = df[
        (df['State'] == selected_state) &
        (df['Season'] == selected_season) &
        (df['Crop_Year'] == selected_year)
    ]

    chart_paths = []
    for f in os.listdir(CHARTS_DIR):
        os.remove(os.path.join(CHARTS_DIR, f))

    if not filtered.empty:
        crop_production = filtered.groupby('Crop')['Production'].sum().sort_values(ascending=True)

        if len(crop_production) > 1:
            crops = crop_production.index.tolist()
            values = crop_production.values.tolist()
            cmap = plt.cm.get_cmap('Set3', len(crops))
            colors = [cmap(i) for i in range(len(crops))]

            plt.figure(figsize=(28, 14))
            bars = plt.barh(crops, values, color=colors, edgecolor='black')
            plt.xlabel("Total Production (tonnes)", fontsize=18)
            plt.ylabel("Crops", fontsize=18)
            plt.title(f"Crop Production in {selected_state} ({selected_season}, {selected_year})", fontsize=22)

            for bar in bars:
                width = bar.get_width()
                plt.text(width + max(values)*0.01, bar.get_y() + bar.get_height()/2, f"{int(width):,}", va='center', fontsize=14)

            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor=colors[i], edgecolor='black', label=crops[i]) for i in range(len(crops))]
            plt.legend(handles=legend_elements, title='Crops', loc='center left', bbox_to_anchor=(1, 0.5), fontsize=12)

            plt.tight_layout()
            path = f'{CHARTS_DIR}/crop_bar_{selected_state}_{selected_year}.png'
            plt.savefig(path, bbox_inches='tight', dpi=200)
            chart_paths.append(path.replace('static/', ''))
            plt.close()

    return render_template(
        'visualization.html',
        chart_paths=chart_paths,
        states=states,
        seasons=seasons,
        years=years,
        selected_state=selected_state,
        selected_season=selected_season,
        selected_year=selected_year
    )

@app.route('/state/<state_name>')
def state_page(state_name):
    return render_template(f'states/{state_name}.html', state_name=state_name)

@app.route('/chart/<path:state_name>.png')
def state_chart(state_name):
    try:
        # Safe and dynamic CSV path
        csv_path = os.path.join(os.path.dirname(__file__), 'India_Agriculture.csv')

        # Read and clean data
        df = pd.read_csv(csv_path, low_memory=False)
        df.columns = df.columns.str.strip()

        df['Production'] = pd.to_numeric(df['Production'], errors='coerce')
        df['Crop_Year'] = pd.to_numeric(df['Crop_Year'], errors='coerce')

        # Normalize state name
        clean_name = state_name.replace('-', ' ').strip().lower()

        # Filter rows for the state
        filtered = df[df['State'].str.strip().str.lower() == clean_name]
        filtered = filtered[filtered['Crop_Year'] >= 2010]

        if filtered.empty:
            print(f"[WARN] No data found for state: {clean_name}")
            abort(404)

        yearly_production = (
            filtered.groupby('Crop_Year')['Production']
            .sum()
            .sort_index()
        )

        # Generate chart
        plt.figure(figsize=(12, 6))
        plt.plot(yearly_production.index, yearly_production.values, marker='o', color='green', linewidth=2)
        plt.title(f'Total Crop Production in {clean_name.title()} (2010–Recent)', fontsize=16)
        plt.xlabel('Year')
        plt.ylabel('Total Production (Tonnes)')
        plt.grid(True)
        plt.tight_layout()

        img = BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        img.seek(0)

        return send_file(img, mimetype='image/png')

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error generating chart for {state_name}: {str(e)}", 500

@app.route('/ai-prediction', methods=['GET', 'POST'])
def airecomm():
    return render_template('airecomm.html')
@app.route('/schemes')
def schemes():
    return render_template('schemes.html')

if __name__ == '__main__':
    print("\u2705 Flask running at http://127.0.0.1:5050")
    app.run(debug=True, port=5050)