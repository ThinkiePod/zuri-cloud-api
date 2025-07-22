# Load navbar from template
def load_navbar_and_footer_html():
    with open("templates/navbar.html", "r") as f:
        navbar_html = f.read()
        
    with open("templates/footer.html", "r") as f:
        footer_html = f.read()
    return navbar_html, footer_html

# Update the background color in docs and redoc pages
def add_custom_color(color: str):
    custom_css = f"""
        <style>
            body {{ background-color: {color} !important; }}
        </style>
        """
    return custom_css
    