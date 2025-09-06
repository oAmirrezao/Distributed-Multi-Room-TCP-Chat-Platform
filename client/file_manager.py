import os
import json
import base64
from pathlib import Path

class FileManager:
    def __init__(self, download_dir='downloads'):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.active_transfers = {}
        self.chunk_size = 4096  # 4KB chunks
    
    def prepare_file(self, file_path):
        try:
            path = Path(file_path)
            if not path.exists():
                print(f"File not found: {file_path}")
                return None
            
            file_size = path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                print("File too large (max 10MB)")
                return None
            
            chunks = []
            transfer_id = os.urandom(16).hex()
            
            with open(path, 'rb') as f:
                chunk_num = 0
                while True:
                    data = f.read(self.chunk_size)
                    if not data:
                        break
                    
                    chunk = {
                        'transfer_id': transfer_id,
                        'filename': path.name,
                        'chunk_num': chunk_num,
                        'total_chunks': -1,  # Will be set later
                        'data': base64.b64encode(data).decode('utf-8')
                    }
                    chunks.append(chunk)
                    chunk_num += 1
            
            # Set total chunks
            for chunk in chunks:
                chunk['total_chunks'] = len(chunks)
            
            print(f"Prepared {len(chunks)} chunks for {path.name}")
            return chunks
            
        except Exception as e:
            print(f"Error preparing file: {e}")
            return None
    
    def receive_chunk(self, chunk_data):
        transfer_id = chunk_data['transfer_id']
        
        if transfer_id not in self.active_transfers:
            self.active_transfers[transfer_id] = {
                'filename': chunk_data['filename'],
                'chunks': {},
                'total_chunks': chunk_data['total_chunks']
            }
        
        transfer = self.active_transfers[transfer_id]
        transfer['chunks'][chunk_data['chunk_num']] = base64.b64decode(chunk_data['data'])
        
        # Check if transfer is complete
        if len(transfer['chunks']) == transfer['total_chunks']:
            return self._complete_transfer(transfer_id)
        
        return False
    
    def _complete_transfer(self, transfer_id):
        transfer = self.active_transfers[transfer_id]
        
        # Reassemble file
        file_path = self.download_dir / transfer['filename']
        
        # Add number if file exists
        if file_path.exists():
            base = file_path.stem
            ext = file_path.suffix
            counter = 1
            while file_path.exists():
                file_path = self.download_dir / f"{base}_{counter}{ext}"
                counter += 1
        
        try:
            with open(file_path, 'wb') as f:
                for i in range(transfer['total_chunks']):
                    f.write(transfer['chunks'][i])
            
            del self.active_transfers[transfer_id]
            print(f"File saved: {file_path}")
            return True
            
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
