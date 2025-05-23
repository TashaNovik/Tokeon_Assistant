import pytest
import os
import numpy as np
from unittest.mock import patch, mock_open, MagicMock

from knowledge_base_api.clients.chunking import chunking, knowledge_base_runner

def test_chunking(temp_file, mock_kb_settings):
    file_dir = os.path.dirname(temp_file)
    file_name = os.path.basename(temp_file)
    
    mock_file_content = "Тестовый контент для базы знаний.\nЭто тестовый файл.\nТокеон - это компания."
    
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
    
    with patch('builtins.open', mock_open(read_data=mock_file_content)), \
         patch('knowledge_base_api.clients.chunking.get_model', return_value=mock_model):
        result = chunking(file_dir, file_name)
        
        assert "Large" in result
        assert "Small" in result
        
        assert len(result["Large"]) > 0
        assert len(result["Small"]) > 0
        
        for chunk in result["Large"]:
            assert hasattr(chunk, "id")
            assert hasattr(chunk, "vector")
            assert hasattr(chunk, "payload")
            
        for small_chunk in result["Small"]:
            assert hasattr(small_chunk, "id")
            assert hasattr(small_chunk, "vector")
            assert hasattr(small_chunk, "payload")

def test_knowledge_base_runner_single_file(temp_file, mock_kb_settings):
    file_dir = os.path.dirname(temp_file)
    file_name = os.path.basename(temp_file)
    file_name_without_ext = os.path.splitext(file_name)[0]
    
    with patch('os.walk') as mock_walk:
        mock_walk.return_value = [
            (file_dir, [], [file_name])
        ]
        
        result = knowledge_base_runner(file_dir)
        
        assert file_name_without_ext in result
        assert os.path.join(file_dir, file_name) in result.values() or file_dir in result.values()

def test_knowledge_base_runner_multiple_files(temp_directory, mock_kb_settings):
    file_names = ["file1.txt", "file2.txt", "file3.txt"]
    for name in file_names:
        file_path = os.path.join(temp_directory, name)
        with open(file_path, "w") as f:
            f.write(f"Содержимое файла {name}")
    
    with patch('os.walk') as mock_walk:
        mock_walk.return_value = [
            (temp_directory, [], file_names + ["test_file.txt"])
        ]
        
        result = knowledge_base_runner(temp_directory)
        
        for name in file_names + ["test_file.txt"]:
            name_without_ext = os.path.splitext(name)[0]
            assert name_without_ext in result
            
        assert len(result) == len(file_names) + 1

def test_knowledge_base_runner_recursive(temp_directory, mock_kb_settings):
    subdir = os.path.join(temp_directory, "subdir")
    os.makedirs(subdir, exist_ok=True)
    
    subdir_file = os.path.join(subdir, "subdir_file.txt")
    with open(subdir_file, "w") as f:
        f.write("Содержимое файла в поддиректории")
    
    with patch('os.walk') as mock_walk:
        mock_walk.return_value = [
            (temp_directory, ["subdir"], ["root_file.txt"]),
            (subdir, [], ["subdir_file.txt"])
        ]
        
        result = knowledge_base_runner(temp_directory)
        
        assert "root_file" in result
        assert "subdir_file" in result
        
        assert temp_directory in str(result["root_file"])
        assert subdir in str(result["subdir_file"]) 