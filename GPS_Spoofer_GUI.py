import sys
import subprocess
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QPushButton, QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot

from GPS_Spoofer import GPS_Spoofer

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
        self.setWindowIcon(QIcon("icone.jpg"))

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
        layout.addWidget(self.stop_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.coord_receiver = CoordinateReceiver()

        self.channel = QWebChannel()
        self.channel.registerObject("coordReceiver", self.coord_receiver)
        self.view.page().setWebChannel(self.channel)

        self.transmission_flowgraph = None

        self.load_map()

    def load_map(self):
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

    def confirm_coordinates(self):
        lat = self.coord_receiver.latitude
        lon = self.coord_receiver.longitude

        if lat is None or lon is None:
            QMessageBox.warning(self, "Erro", "Por favor selecione as coordenadas no mapa.")
            return

        working_dir = "C:/Universidade/GPS Spoofer/gps-sdr-sim-master"

        # gcc_path = r"C:\mingw64\bin\gcc.exe"
        # compile_cmd = [gcc_path, "gpssim.c", "-lm", "-O3", "-o", "gps-sdr-sim"]
        #
        # try:
        #    subprocess.run(compile_cmd, cwd=working_dir, check=True)
        # except FileNotFoundError:
        #     QMessageBox.critical(self,"Erro","Não foi possível encontrar o compilador 'gcc'. Verifica se o MinGW/compilador está instalado e no PATH.")

        sim_exe = os.path.join(working_dir, "gps-sdr-sim.exe")

        sim_cmd = [
            sim_exe, "-b", "8", "-e", "brdc3390.25n",
            "-l", f"{lat},{lon},100"
        ]

        try:
            subprocess.run(sim_cmd, cwd=working_dir, check=True)
            QMessageBox.information(self, "Sucesso", "Ficheiro gpssim.bin gerado com sucesso.")
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Erro", "Erro ao executar o gps-sdr-sim.")

    def start_transmission(self):
        if self.transmission_flowgraph is None:
            self.transmission_flowgraph = GPS_Spoofer()
            self.transmission_flowgraph.start()
            self.transmission_flowgraph.show()
        else:
            QMessageBox.information(self, "Aviso", "Transmissão já está em curso.")

    def stop_transmission(self):
        if self.transmission_flowgraph:
            self.transmission_flowgraph.stop()
            self.transmission_flowgraph.wait()
            self.transmission_flowgraph.close()
            self.transmission_flowgraph = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GPSWindow()
    window.show()
    sys.exit(app.exec_())
