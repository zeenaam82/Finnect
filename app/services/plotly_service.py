import plotly.graph_objects as go

def create_defect_pie(stats: dict):
    labels = ["normal", "defect"]
    values = [stats.get("num_customers", 0) - stats.get("num_defects", 0),
              stats.get("num_defects", 0)]

    fig = go.Figure(
        data=[go.Pie(labels=labels, values=values, hovertemplate="category=%{label}<br>count=%{value}<extra></extra>")],
        layout_title_text="불량률 분포"
    )
    return fig
