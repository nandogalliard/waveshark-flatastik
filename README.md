# waveshark-flatastik

This file is intended to be run in e-Paper/RaspberryPi_JetsonNano/python/examples with e-paper being the repository https://github.com/waveshare/e-Paper.

One needs to create a local file called secets_api_etc.py which includes a dictionary called wg and wg_offset. The dic wg containes the key of the useraccounts in the wg with the corresponding values being the names of the flatmates as a string.

Flattastik doesn't reset the work counter in the backend which is why the wg_offset is needed. It is a dictionary with the same keys as wg and the values are the number work points that need to be offset to have it start at zero. If you don't want to offset anything, just set the values to zero.

Lastly api key x_api_key and a wg_name are needed as string. You can find this key when loading the flatastik webapp at https://www.flatastic-app.com/webapp/ in the developer console of your browser. The key is the value of the cookie called "x-api-key".
