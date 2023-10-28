from PyQt5.QtWidgets import QFileDialog
import os

def loadCSVFile(parent):
    current_directory = os.path.join(os.getcwd(), "datasets")  # Set the current directory to "datasets"
    
    options = QFileDialog.Options()
    options |= QFileDialog.ReadOnly
    options |= QFileDialog.ExistingFile

    file_dialog = QFileDialog.getOpenFileName(
        parent, "Select CSV File", current_directory, "CSV Files (*.csv);;All Files (*)", options=options
    )

    if file_dialog[0]:
        selected_file = file_dialog[0]
        file_name = os.path.basename(selected_file)
        parent.labelSignal.setText(os.path.splitext(file_name)[0])
