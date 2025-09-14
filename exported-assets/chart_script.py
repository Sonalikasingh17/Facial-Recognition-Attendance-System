import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Data
data = {
  "algorithms": [
    {
      "name": "OpenCV Haar Cascade",
      "accuracy": 84.5,
      "speed_rating": 9,
      "memory_usage": 2,
      "use_case": "Real-time applications"
    },
    {
      "name": "dlib HOG",
      "accuracy": 87.2,
      "speed_rating": 8,
      "memory_usage": 5,
      "use_case": "Balanced performance"
    },
    {
      "name": "OpenCV DNN",
      "accuracy": 92.3,
      "speed_rating": 6,
      "memory_usage": 6,
      "use_case": "High accuracy needed"
    },
    {
      "name": "dlib CNN",
      "accuracy": 94.8,
      "speed_rating": 3,
      "memory_usage": 8,
      "use_case": "Maximum accuracy"
    },
    {
      "name": "MTCNN",
      "accuracy": 96.1,
      "speed_rating": 2,
      "memory_usage": 9,
      "use_case": "Research/offline"
    }
  ]
}

# Convert to DataFrame
df = pd.DataFrame(data['algorithms'])

# Normalize all metrics to 0-100 scale
# Accuracy: already in percentage (0-100)
df['accuracy_norm'] = df['accuracy']

# Speed rating: higher is better, normalize 2-9 to 0-100
speed_min, speed_max = df['speed_rating'].min(), df['speed_rating'].max()
df['speed_norm'] = ((df['speed_rating'] - speed_min) / (speed_max - speed_min)) * 100

# Memory efficiency: lower memory usage is better, so invert to show efficiency
memory_min, memory_max = df['memory_usage'].min(), df['memory_usage'].max()
df['memory_eff_norm'] = ((memory_max - df['memory_usage']) / (memory_max - memory_min)) * 100

# Create radar chart
fig = go.Figure()

# Define colors from the brand palette
colors = ['#1FB8CD', '#DB4545', '#2E8B57', '#5D878F', '#D2BA4C']

# Create traces for each algorithm
for i, (_, row) in enumerate(df.iterrows()):
    # Abbreviate algorithm names for display while keeping them clear
    name_abbrev = row['name'].replace('OpenCV ', '').replace('dlib ', '')
    if len(name_abbrev) > 15:
        name_abbrev = name_abbrev[:12] + '...'
    
    fig.add_trace(go.Scatterpolar(
        r=[row['accuracy_norm'], row['speed_norm'], row['memory_eff_norm']],
        theta=['Accuracy (%)', 'Speed (1-10)', 'Memory Eff'],
        fill='toself',
        name=name_abbrev,
        line_color=colors[i],
        fillcolor=colors[i],
        opacity=0.4,
        line_width=2,
        customdata=[[row['accuracy'], row['speed_rating'], memory_max + memory_min - row['memory_usage']]],
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Accuracy: %{customdata[0]:.1f}%<br>' +
                     'Speed: %{customdata[1]}/10<br>' +
                     'Memory Usage: %{customdata[2]}GB<br>' +
                     '<extra></extra>'
    ))

# Update layout
fig.update_layout(
    title='Face Detection Performance Metrics',
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100],
            tickmode='linear',
            tick0=0,
            dtick=25,
            ticksuffix='',
            showticklabels=True
        ),
        angularaxis=dict(
            tickfont_size=11,
            rotation=90
        )
    ),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.05,
        xanchor='center',
        x=0.5
    ),
    showlegend=True
)

# Save as PNG and SVG
fig.write_image("face_detection_radar.png")
fig.write_image("face_detection_radar.svg", format="svg")

fig.show()