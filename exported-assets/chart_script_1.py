import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Component data with better positioning to avoid crossings
components_data = {
    "name": ["Camera Input", "Face Detection", "Face Recognition", "Attendance Manager", "Database Storage", "Web Interface", "Reporting System"],
    "type": ["input", "processing", "processing", "business", "storage", "interface", "output"],
    "x": [1, 2.5, 4, 5.5, 5.5, 1, 7],
    "y": [3, 3, 3, 3, 1.5, 1.5, 1.5],
    "short_name": ["Camera", "Detection", "Recognition", "Attendance", "Database", "Web UI", "Reports"],
    "details": [
        "Live video feed",
        "HOG: 87%, CNN: 95%",
        "99.83% accuracy",
        "Mark attendance",
        "CSV/SQLite storage", 
        "Streamlit dashboard",
        "Analytics & exports"
    ]
}

# Create DataFrame
df = pd.DataFrame(components_data)

# Define colors for each component type
color_map = {
    "input": "#1FB8CD",      # Strong cyan
    "processing": "#DB4545",  # Bright red  
    "business": "#2E8B57",    # Sea green
    "storage": "#5D878F",     # Cyan
    "interface": "#D2BA4C",   # Moderate yellow
    "output": "#B4413C"       # Moderate red
}

# Create figure
fig = go.Figure()

# Add rectangular boxes for each component
for i, row in df.iterrows():
    # Add rectangle shape
    fig.add_shape(
        type="rect",
        x0=row['x']-0.4, y0=row['y']-0.3,
        x1=row['x']+0.4, y1=row['y']+0.3,
        fillcolor=color_map[row['type']],
        line=dict(color='white', width=2),
        opacity=0.9
    )
    
    # Add text label
    fig.add_annotation(
        x=row['x'], y=row['y'],
        text=f"<b>{row['short_name']}</b>",
        showarrow=False,
        font=dict(color='white', size=12),
        align="center"
    )

# Data flow connections with labels
flow_data = [
    {"from": (1, 3), "to": (2.5, 3), "label": "Video frames", "path": "straight"},
    {"from": (2.5, 3), "to": (4, 3), "label": "Face locations", "path": "straight"},
    {"from": (4, 3), "to": (5.5, 3), "label": "Person ID", "path": "straight"},
    {"from": (5.5, 3), "to": (5.5, 1.5), "label": "Records", "path": "down"},
    {"from": (5.5, 1.5), "to": (7, 1.5), "label": "Data", "path": "straight"},
    {"from": (1, 1.5), "to": (2.5, 3), "label": "Commands", "path": "up"},
    {"from": (5.5, 1.5), "to": (1, 1.5), "label": "Display data", "path": "curved"}
]

# Add flow arrows and labels
for flow in flow_data:
    x1, y1 = flow["from"]
    x2, y2 = flow["to"]
    
    if flow["path"] == "straight":
        # Straight arrow
        fig.add_shape(
            type="line",
            x0=x1+0.4 if x2 > x1 else x1-0.4, y0=y1,
            x1=x2-0.4 if x2 > x1 else x2+0.4, y1=y2,
            line=dict(color="#13343B", width=2),
            opacity=0.7
        )
        
        # Arrow head
        if x2 > x1:  # Right arrow
            fig.add_shape(
                type="path",
                path=f"M {x2-0.5},{y2-0.1} L {x2-0.4},{y2} L {x2-0.5},{y2+0.1} Z",
                fillcolor="#13343B", line=dict(color="#13343B", width=0)
            )
            label_x, label_y = (x1+x2)/2, y1+0.15
        else:  # Left arrow
            fig.add_shape(
                type="path", 
                path=f"M {x2+0.5},{y2-0.1} L {x2+0.4},{y2} L {x2+0.5},{y2+0.1} Z",
                fillcolor="#13343B", line=dict(color="#13343B", width=0)
            )
            label_x, label_y = (x1+x2)/2, y1+0.15
            
    elif flow["path"] == "down":
        # Vertical down arrow
        fig.add_shape(
            type="line",
            x0=x1, y0=y1-0.3, x1=x2, y1=y2+0.3,
            line=dict(color="#13343B", width=2),
            opacity=0.7
        )
        fig.add_shape(
            type="path",
            path=f"M {x2-0.1},{y2+0.4} L {x2},{y2+0.3} L {x2+0.1},{y2+0.4} Z",
            fillcolor="#13343B", line=dict(color="#13343B", width=0)
        )
        label_x, label_y = x1+0.2, (y1+y2)/2
        
    elif flow["path"] == "up":
        # Diagonal up arrow
        fig.add_shape(
            type="line",
            x0=x1+0.4, y0=y1+0.3, x1=x2-0.4, y1=y2-0.3,
            line=dict(color="#13343B", width=2),
            opacity=0.7
        )
        fig.add_shape(
            type="path",
            path=f"M {x2-0.5},{y2-0.2} L {x2-0.4},{y2-0.3} L {x2-0.3},{y2-0.2} Z",
            fillcolor="#13343B", line=dict(color="#13343B", width=0)
        )
        label_x, label_y = (x1+x2)/2, (y1+y2)/2+0.2
        
    elif flow["path"] == "curved":
        # Curved arrow for long connection
        fig.add_shape(
            type="path",
            path=f"M {x1-0.4},{y1} Q {(x1+x2)/2},{y1-0.8} {x2+0.4},{y2}",
            line=dict(color="#13343B", width=2),
            opacity=0.7
        )
        fig.add_shape(
            type="path",
            path=f"M {x2+0.5},{y2-0.1} L {x2+0.4},{y2} L {x2+0.5},{y2+0.1} Z",
            fillcolor="#13343B", line=dict(color="#13343B", width=0)
        )
        label_x, label_y = (x1+x2)/2, y1-0.5
    
    # Add flow label
    fig.add_annotation(
        x=label_x, y=label_y,
        text=flow["label"],
        showarrow=False,
        font=dict(color="#13343B", size=9),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#13343B",
        borderwidth=1
    )

# Create invisible traces for legend
for comp_type, color in color_map.items():
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(color=color, size=15, symbol='square'),
        name=comp_type.title(),
        showlegend=True
    ))

# Update layout
fig.update_layout(
    title="Face Recognition System Architecture",
    showlegend=True,
    legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='center', x=0.5),
    plot_bgcolor='white',
    paper_bgcolor='white'
)

# Update axes
fig.update_xaxes(
    title="",
    showgrid=False,
    showticklabels=False,
    zeroline=False,
    range=[0, 8]
)

fig.update_yaxes(
    title="",
    showgrid=False,
    showticklabels=False, 
    zeroline=False,
    range=[0.5, 4]
)

# Save the chart
fig.write_image("architecture_diagram.png")
fig.write_image("architecture_diagram.svg", format="svg")

print("Professional system architecture diagram created successfully!")