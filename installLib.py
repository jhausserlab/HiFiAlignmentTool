import sys
import subprocess

print('Installing all the libraries required to run the code')
# implement pip as a subprocess:
print(' ------------- Installing Numpy ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'numpy'])
print(' ------------- Installing tifffile ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'tifffile'])
print(' ------------- Installing aicspylibczi ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'aicspylibczi'])
print(' ------------- Installing scikit-image ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'scikit-image'])
print(' ------------- Installing pystackreg ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pystackreg'])
print(' ------------- Installing pandas ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pandas'])
print(' ------------- FINISHED ------------- ')
