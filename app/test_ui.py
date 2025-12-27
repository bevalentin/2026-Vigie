from nicegui import ui

@ui.page('/')
def index():
    ui.label('It works!').classes('text-4xl text-green-500 m-auto')

ui.run(port=8081, show=False)
