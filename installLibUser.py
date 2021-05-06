import sys
import subprocess

print('Installing all the libraries required to run the code')
# implement pip as a subprocess:
print(' ------------- Installing Numpy ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'numpy'])
print(' ------------- Installing tifffile ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'tifffile'])
print(' ------------- Installing aicspylibczi ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'aicspylibczi'])
print(' ------------- Installing scikit-image ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'scikit-image'])
print(' ------------- Installing pystackreg ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'pystackreg'])
print(' ------------- Installing pandas ------------- ')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'pandas'])
print(' ------------- FINISHED ------------- ')

