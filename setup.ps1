python -m venv .\venv
pip install -r .\requirements.txt
Set-Location .\app
$env:PYTHONPATH = $PWD
