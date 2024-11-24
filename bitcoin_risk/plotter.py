import plotly.graph_objects as go
import plotly.express as px

def bitcoin_plot(btc):

    def add_colordropdown(fig):
        colorscales = ['Plotly3', 'Viridis', 'Rainbow', 'Jet']
        # Add dropdown menu for colorscales
        fig.update_layout(
            updatemenus=[
                dict(
                    buttons=[
                        dict(
                            label=scale,
                            method="relayout",
                            args=[{"coloraxis.colorscale": scale}] 
                        )
                        for scale in colorscales
                    ],
                    direction="down",
                    showactive=True,
                )
            ]
        )
        return fig

    def add_line(fig, x, y, color, name):
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode='lines',
                name=name,
                line=dict(color=color, width=1),
                yaxis='y',
                showlegend=False
            )
        )
        return fig

    # Create the scatter plot for the 'open' prices colored by 'risk'
    fig = px.scatter(
        btc,
        x='date',
        y='usd',
        color='risk',  # Color the scatter points by the 'risk' column
        title='Bitcoin Logarithmic Regression Risk Metric',
        color_continuous_scale='Turbo'
    )

    # future = btc[btc['date'] > '2024-11-01']
    future = btc
    # add_line(fig, future['date'], future['fit'], 'rgba(000, 200, 000, 0.4)', 'top')
    add_line(fig, future['date'], future['top'], 'rgba(200, 000, 000, 0.4)', 'top')
    add_line(fig, future['date'], future['undervalued'], 'rgba(0, 000, 200, 0.4)', 'bottom')

    # Convert the figure to a Plotly Graph Object figure to add a second axis
    fig = go.Figure(fig)

    # Add a second trace for the 'risk' values
    fig.add_trace(
        go.Scatter(
            x=btc['date'],
            y=btc['risk'],
            mode='lines',
            name='Risk',
            # line=dict(color='grey'),
            line=dict(color='rgba(50, 50, 50, 0.3)'),  # Red color with transparency
            yaxis='y2',
            showlegend=False,
        )
    )
    fig.update_layout(coloraxis=dict(cmin=-0.1,  cmax=1))

    # Update the layout to include a second y-axis
    fig.update_layout(
        yaxis=dict(
            title='Price / $',
            type='log'  # Log scale for the open price
        ),
        yaxis2=dict(
            title='Risk',
            overlaying='y',  # Overlay on the same plot
            side='right',    # Place it on the right
            type='linear',    # Make the second y-axis linear
            showgrid=False
        ),
        hovermode='x unified'
    )

    add_colordropdown(fig)

    return fig
