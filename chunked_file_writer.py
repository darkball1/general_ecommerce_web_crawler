import os

class ChunkedFileWriter:
    def __init__(self, filename_prefix, max_file_size=5 * 1024 * 1024):  
        self.filename_prefix = filename_prefix
        self.max_file_size = max_file_size
        self.current_file = None
        self.current_size = 0
        self.file_count = 0

    def write(self, data):
        # Check if a new file needs to be opened (no file or file size limit exceeded)
        if self.current_file is None or self.current_size >= self.max_file_size:
            self.open_new_file()

        self.current_file.write(data) 
        self.current_size += len(data)

    def open_new_file(self):
        # Close the current file if it exists
        if self.current_file:
            self.current_file.close()

        # Increment file count and create a new file
        self.file_count += 1
        new_filename = f"{self.filename_prefix}_{self.file_count:04d}.txt"
        os.makedirs(os.path.dirname(new_filename), exist_ok=True)  
        self.current_file = open(new_filename, 'w')  
        self.current_size = 0  

    def close(self):
        # Close the current file if it is open
        if self.current_file:
            self.current_file.close()
