import sys
import os
import subprocess  # Apenas para o gerador, não para a transmissão
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QPushButton, QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, QThread, pyqtSignal, Qt

# --- IMPORTANTE: Importar a tua classe do GNU Radio ---
# Certifica-te que o ficheiro GPS_Spoofer.py está na mesma pasta
from GPS_Spoofer import GPS_Spoofer


# --- Worker 1: Gerador de BIN (Mantém-se igual) ---
class BinGeneratorWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, command, working_dir):
        super().__init__()
        self.command = command
        self.working_dir = working_dir

    def run(self):
        try:
            subprocess.run(self.command, cwd=self.working_dir, check=True)
            self.finished.emit()
        except subprocess.CalledProcessError:
            self.error.emit("Erro ao executar o simulador GPS.")
        except Exception as e:
            self.error.emit(f"Erro inesperado: {str(e)}")


# --- Worker 2: Transmissão via GNU Radio ---
class GnuradioTxWorker(QThread):
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.tb = None  # Top Block

    def run(self):
        try:
            # 1. Instanciar a classe do GNU Radio
            # Se o teu fluxo precisa do caminho do ficheiro, passa-o aqui.
            # Exemplo: self.tb = GPS_Spoofer(file_path="C:/.../gpssim.bin")
            self.tb = GPS_Spoofer()

            # 2. Iniciar o fluxo
            self.tb.start()

            # 3. Esperar que o fluxo termine (Bloqueia ESTA thread, não a GUI)
            self.tb.wait()

            # Se passar daqui, o fluxo terminou (ficheiro acabou ou foi parado)
            self.finished.emit()

        except Exception as e:
            self.error.emit(f"Erro no fluxo GNU Radio: {str(e)}")

    def stop(self):
        if self.tb:
            # Pára o fluxo graciosamente
            self.tb.stop()
            self.tb.wait()  # Garante que fechou
            self.tb = None


class CoordinateReceiver(QObject):
    def __init__(self):
        super().__init__()
        self.latitude = None
        self.longitude = None

    @pyqtSlot(float, float)
    def setCoordinates(self, lat, lon):
        self.latitude = lat
        self.longitude = lon


class GPSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPS Spoofer")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon("gui_icon.png"))

        layout = QVBoxLayout()
        self.view = QWebEngineView()
        layout.addWidget(self.view)

        self.button = QPushButton("Confirmar coordenadas")
        self.button.clicked.connect(self.confirm_coordinates)
        layout.addWidget(self.button)

        self.transmit_button = QPushButton("Iniciar Transmissão")
        self.transmit_button.clicked.connect(self.start_transmission)
        layout.addWidget(self.transmit_button)

        self.stop_button = QPushButton("Parar Transmissão")
        self.stop_button.clicked.connect(self.stop_transmission)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.coord_receiver = CoordinateReceiver()
        self.channel = QWebChannel()
        self.channel.registerObject("coordReceiver", self.coord_receiver)
        self.view.page().setWebChannel(self.channel)

        self.gen_worker = None
        self.tx_worker = None

        self.load_map()

    def load_map(self):
        # (O teu código do mapa - inalterado)
        map_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset=\"utf-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
            <style>html, body, #map {{ height: 100%; margin: 0; padding: 0; }}</style>
            <script src=\"https://cdn.jsdelivr.net/npm/leaflet@1.7.1/dist/leaflet.js\"></script>
            <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet@1.7.1/dist/leaflet.css\" />
            <script src=\"qrc:///qtwebchannel/qwebchannel.js\"></script>
        </head>
        <body>
            <div id=\"map\"></div>
            <script>
                var map = L.map('map').setView([38.736946, -9.142685], 6);
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: 'Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
                    maxZoom: 18
                }}).addTo(map);

                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    var receiver = channel.objects.coordReceiver;
                    map.on('click', function(e) {{
                        L.popup()
                         .setLatLng(e.latlng)
                         .setContent("Latitude: " + e.latlng.lat.toFixed(5) + "<br>Longitude: " + e.latlng.lng.toFixed(5))
                         .openOn(map);
                        receiver.setCoordinates(e.latlng.lat, e.latlng.lng);
                    }});
                }});
            </script>
        </body>
        </html>
        """
        self.view.setHtml(map_html)

    # --- Lógica de Geração (Processo Externo) ---
    def confirm_coordinates(self):
        lat = self.coord_receiver.latitude
        lon = self.coord_receiver.longitude
        if lat is None:
            QMessageBox.warning(self, "Erro", "Selecione coordenadas.")
            return

        working_dir = "C:/Universidade/GPS Spoofer/gps-sdr-sim-master"
        sim_exe = os.path.join(working_dir, "gps-sdr-sim.exe")
        sim_cmd = [sim_exe, "-b", "8", "-e", "brdc3390.25n", "-l", f"{lat},{lon},100"]

        self.button.setEnabled(False)
        self.button.setText("A Gerar Ficheiro BIN...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        self.gen_worker = BinGeneratorWorker(sim_cmd, working_dir)
        self.gen_worker.finished.connect(self.on_gen_finished)
        self.gen_worker.error.connect(self.on_gen_error)
        self.gen_worker.start()

    def on_gen_finished(self):
        self.button.setEnabled(True)
        self.button.setText("Confirmar coordenadas")
        QApplication.restoreOverrideCursor()
        QMessageBox.information(self, "Sucesso", "Ficheiro BIN gerado com sucesso.")

    def on_gen_error(self, msg):
        self.button.setEnabled(True)
        self.button.setText("Confirmar coordenadas")
        QApplication.restoreOverrideCursor()
        QMessageBox.critical(self, "Erro", msg)

    # --- Lógica de Transmissão (GNU Radio) ---
    def start_transmission(self):
        # Verificar ficheiro
        bin_path = "C:/Universidade/GPS Spoofer/gps-sdr-sim-master/gpssim.bin"
        if not os.path.exists(bin_path):
            QMessageBox.warning(self, "Erro", "Gere o ficheiro BIN primeiro.")
            return

        if self.tx_worker is not None and self.tx_worker.isRunning():
            return

        self.transmit_button.setEnabled(False)
        self.transmit_button.setText("A Transmitir via GNU Radio...")
        self.stop_button.setEnabled(True)

        # Inicia a Thread do GNU Radio
        self.tx_worker = GnuradioTxWorker()
        self.tx_worker.finished.connect(self.on_tx_finished)
        self.tx_worker.error.connect(self.on_tx_error)
        self.tx_worker.start()

    def stop_transmission(self):
        if self.tx_worker:
            # Chama o metodo stop() da thread, que para o flowgraph
            self.tx_worker.stop()
            self.tx_worker.quit()
            self.tx_worker.wait()  # Aguarda limpeza da thread
            self.tx_worker = None

        self.reset_tx_ui()

    def on_tx_finished(self):
        self.reset_tx_ui()
        # Opcional: Avisar que acabou
        # QMessageBox.information(self, "Info", "Transmissão GNU Radio terminada.")

    def on_tx_error(self, msg):
        self.stop_transmission()
        QMessageBox.critical(self, "Erro GNU Radio", msg)

    def reset_tx_ui(self):
        self.transmit_button.setEnabled(True)
        self.transmit_button.setText("Iniciar Transmissão")
        self.stop_button.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GPSWindow()
    window.show()
    sys.exit(app.exec_())
