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

# Título de panel sin borde/fondo
PANEL_TITLE_STYLE = """
    color: #2D3748; 
    font-size: 18px; 
    font-weight: 600;
    background: transparent;
    border: none;
    padding: 0;
"""

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

# ComboBox mejorado con dropdown bonito
COMBO_BOX_STYLE = """
    QComboBox {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 10px 16px;
        color: #2D3748;
        font-size: 14px;
        min-width: 200px;
    }
    QComboBox:hover {
        border-color: #CBD5E0;
        background-color: #F7FAFC;
    }
    QComboBox:focus {
        border-color: #4299E1;
        background-color: white;
    }
    QComboBox::drop-down {
        border: none;
        width: 30px;
    }
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #718096;
        margin-right: 8px;
    }
    QComboBox::down-arrow:hover {
        border-top-color: #2D3748;
    }
    QComboBox QAbstractItemView {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 4px;
        selection-background-color: #EDF2F7;
        selection-color: #2D3748;
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        padding: 8px 16px;
        border-radius: 6px;
        min-height: 32px;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: #F7FAFC;
    }
    QComboBox QAbstractItemView::item:selected {
        background-color: #EDF2F7;
        color: #2D3748;
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

# Estilo para labels de configuración (sin borde)
SETTING_LABEL_STYLE = """
    color: #4A5568;
    font-size: 14px;
    font-weight: 500;
    background: transparent;
    border: none;
    padding: 0;
"""

# Estilo para labels de hint (texto pequeño)
HINT_LABEL_STYLE = """
    color: #A0AEC0;
    font-size: 12px;
    background: transparent;
    border: none;
    padding: 0;
"""

# Estilo para label de status
STATUS_LABEL_STYLE = """
    color: #4A5568;
    font-size: 15px;
    font-weight: 500;
    background: transparent;
    border: none;
    margin-left: 8px;
"""
