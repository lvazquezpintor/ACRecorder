"""
Estilos y colores centralizados para la aplicación
"""

# Paleta de colores
COLORS = {
    'bg_primary': '#F7FAFC',
    'bg_white': '#FFFFFF',
    'bg_light': '#EDF2F7',
    'border': '#E2E8F0',
    'text_primary': '#2D3748',
    'text_secondary': '#4A5568',
    'text_muted': '#718096',
    'text_light': '#A0AEC0',
    'accent_red': '#E53E3E',
    'accent_green': '#48BB78',
    'accent_blue': '#4299E1',
    'status_offline': '#EF4444',
    'status_monitoring': '#F59E0B',
    'status_recording': '#10B981',
}

# Estilos de componentes comunes
PANEL_STYLE = """
    QFrame {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
    }
"""

PANEL_TITLE_STYLE = "color: #2D3748; font-size: 18px; font-weight: 600;"

TEXT_EDIT_STYLE = """
    QTextEdit {
        background-color: #F7FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        color: #4A5568;
        font-family: 'Menlo', 'Monaco', monospace;
        font-size: 12px;
        padding: 12px;
    }
"""

COMBO_BOX_STYLE = """
    QComboBox {
        background-color: #F7FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 8px 12px;
        color: #2D3748;
        font-size: 13px;
    }
"""

TREE_WIDGET_STYLE = """
    QTreeWidget {
        background-color: white;
        border: none;
        border-radius: 12px;
        color: #2D3748;
        font-size: 13px;
        padding: 12px;
    }
    QTreeWidget::item {
        padding: 8px;
        border-bottom: 1px solid #F7FAFC;
    }
    QTreeWidget::item:selected {
        background-color: #EDF2F7;
        color: #2D3748;
    }
    QHeaderView::section {
        background-color: #F7FAFC;
        color: #718096;
        padding: 12px;
        border: none;
        font-weight: 600;
        font-size: 12px;
    }
"""

SEARCH_INPUT_STYLE = """
    QLineEdit {
        border: none;
        background: transparent;
        color: #2D3748;
        font-size: 13px;
    }
"""

SIDEBAR_STYLE = """
    QFrame {
        background-color: white;
        border-right: 1px solid #E2E8F0;
    }
"""
