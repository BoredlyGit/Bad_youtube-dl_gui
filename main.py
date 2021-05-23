from PyQt5 import QtWidgets as qt
from PyQt5 import QtCore
import youtube_dl

app = qt.QApplication([])


class QueueFrameEntry(qt.QFrame):
    def __init__(self, **kwargs):
        super().__init__()

        self.setLayout(qt.QHBoxLayout())
        self.setFrameShape(qt.QFrame.Box)
        self.setFrameShadow(qt.QFrame.Sunken)

        for field, text in kwargs.items():
            label = qt.QLabel(text)
            spacer_frame = qt.QFrame()
            spacer_frame.setFrameShadow(qt.QFrame.Sunken)
            spacer_frame.setFrameShape(qt.QFrame.VLine)

            setattr(self, f"{field}_label", label)
            self.layout().addWidget(label)
            self.layout().addWidget(spacer_frame)


class PendingDownload(QueueFrameEntry):
    def __init__(self, url: str, media_format: str):
        self.url = url
        self.media_format = media_format
        self.status = "PENDING"
        self.downloader_thread = None

        super().__init__(url=url, media_format=media_format, status=self.status)

    def __str__(self):
        return self.url

    def update_status(self, new_status, color=None):
        self.status = new_status
        self.status_label.setText(new_status)

    def start_download(self):
        self.downloader_thread = DownloaderQThread(self)
        self.downloader_thread.start()


class DownloaderQThread(QtCore.QThread):
    def __init__(self, pending_download: PendingDownload):
        self.pending_download = pending_download
        super().__init__()

    def run(self):
        def download_progress_hook(progress):
            if progress["status"] == "downloading":
                self.pending_download.update_status(f"{progress['status']}...{progress['_percent_str']}")

        options = {"progress_hooks": [download_progress_hook], "outtmpl": "%(title)s.%(ext)s"}

        if self.pending_download.media_format == "mp3":
            options["postprocessors"] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
        elif self.pending_download.media_format == "mp4":
            options["format"] = "mp4"

        self.pending_download.setStyleSheet("background-color: lightblue")
        with youtube_dl.YoutubeDL(options) as downloader:
            downloader.download([self.pending_download.url])

        self.pending_download.update_status("FINISHED")
        self.pending_download.setStyleSheet("background-color: green")


class QueueFrame(qt.QScrollArea):
    def __init__(self):
        super().__init__()
        self.downloads = []
        self.started_downloads = []
        self.setWidgetResizable(True)

        self.frame = qt.QFrame()
        self.frame.setLayout(qt.QVBoxLayout())
        self.frame.layout().setContentsMargins(5, 0, 5, 0)
        self.frame.layout().setSpacing(0)

        headings_frame = QueueFrameEntry(video_url="Video URL", media_format="Format", status="Status")
        headings_frame.setFixedHeight(50)

        self.frame.layout().addWidget(headings_frame)
        self.frame.setFrameShape(qt.QFrame.Box)
        self.frame.setFrameShadow(qt.QFrame.Sunken)

        self.setWidget(self.frame)

    def add_download(self, download: PendingDownload):
        self.downloads.append(download)
        self.frame.layout().addWidget(download)

    def start_downloads(self):
        for download in self.downloads:
            print(self.started_downloads)
            if (download.url, download.media_format) not in self.started_downloads and download.status == "PENDING":
                download.start_download()
                self.started_downloads.append((download.url, download.media_format))
            elif (download.url, download.media_format) in self.started_downloads and download.status == "PENDING":
                box = qt.QMessageBox(qt.QMessageBox.Warning, "Duplicate URL", f'The pending url "{download.url}" '
                                     f'duplicates an already downloaded file (same url and format), '
                                     f'and is being skipped.')
                box.exec()
                download.update_status("FAILED: Duplicate of already downloaded file")
                download.setStyleSheet("background-color: red")


def main_frame_init():
    main_frame = qt.QFrame()
    main_frame.setLayout(qt.QVBoxLayout())
    # ------------------------------------------------------------------------------
    url_frame = qt.QFrame()
    url_frame.setLayout(qt.QVBoxLayout())
    url_frame.layout().addWidget(qt.QLabel("Paste your url here:"))
    url_input_box = qt.QLineEdit()
    url_frame.layout().addWidget(url_input_box)

    download_options_frame = qt.QFrame()
    download_options_frame.setLayout(qt.QHBoxLayout())

    media_format_selector = qt.QComboBox()
    media_format_selector.addItems(["mp3", "mp4"])
    download_options_frame.layout().addWidget(media_format_selector)

    done_button = qt.QToolButton()
    done_button.setText("Add to queue")
    done_button.pressed.connect(
        lambda: queue_frame.add_download(PendingDownload(url_input_box.text(), media_format_selector.currentText()))
        if len(url_input_box.text()) > 0 else None)
    download_options_frame.layout().addWidget(done_button)
    url_frame.layout().addWidget(download_options_frame)

    url_frame.setFixedHeight(150)
    main_frame.layout().addWidget(url_frame)
    # ------------------------------------------------------------------------------
    queue_frame = QueueFrame()
    main_frame.layout().addWidget(queue_frame)
    # TODO: Merge this into QueueFrame() and add a label
    download_button = qt.QToolButton()
    download_button.setText("Download!")
    download_button.pressed.connect(queue_frame.start_downloads)
    download_button.setFixedSize(75, 25)
    main_frame.layout().addWidget(download_button)

    return main_frame


def main():
    main_frame = main_frame_init()

    main_win = qt.QMainWindow()
    main_win.setCentralWidget(main_frame)
    main_win.show()

    app.exec_()


if __name__ == "__main__":
    main()
