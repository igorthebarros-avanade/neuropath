# utils.py
import textwrap
from tabulate import tabulate

def wrap_text(text, width=70):
    """Helper function to wrap text for better readability."""
    return "\n".join(textwrap.wrap(str(text), width))

def generate_text_bar_chart(data, label_key, value_key, max_width=50, char='█'):
    """Generates a text-based bar chart."""
    if not data:
        return "No data to generate chart."

    # Sort data for better visualization, e.g., by score ascending
    sorted_data = sorted(data, key=lambda x: x.get(value_key, 0))

    max_label_len = max(len(str(item[label_key])) for item in sorted_data)
    chart_lines = []

    for item in sorted_data:
        label = str(item[label_key]).ljust(max_label_len)
        value = item.get(value_key, 0)
        if not isinstance(value, (int, float)):
            value = 0
        
        num_blocks = int((value / 100) * max_width)
        bar = char * num_blocks
        empty_space = ' ' * (max_width - num_blocks)
        
        chart_lines.append(f"{label}: [{bar}{empty_space}] {value}%")
    
    return "\n".join(chart_lines)
