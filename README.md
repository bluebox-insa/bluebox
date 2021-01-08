# Innotech MVP :headphones::zap:

Turn your **Raspberry Pi** into a **Bluetooth hub** to play your music through multiple bluetooth **synced** speakers 🔊🔊🔊.

1. [Requirements 📜](<#Requirements 📜>)
1. [Your path to multi-devices sound on Linux ! 🔥](./installation/README.md)
1. [Run from a fresh Raspberry install 🐍](<#Run from a fresh Raspberry install 🐍>)
1. [Comments](<#Comments>)

## Requirements 📜
- Raspberry pi (model 3B used)
- Up to 4 speakers in bluetooth mode
- 4 bluetooth dongles (tested with Baseus USB Bluetooth adaptateur : https://www.aliexpress.com/item/1005001829990800.html?spm=a2g0o.productlist.0.0.18a03959VMyWgE&algo_pvid=7c0e1fa6-38fd-49ef-9d7c-fb7c29c74d0a&algo_expid=7c0e1fa6-38fd-49ef-9d7c-fb7c29c74d0a-0&btsid=2100bdde16101020065588400ef738&ws_ab_test=searchweb0_0,searchweb201602_,searchweb201603_)
- Smartphone Android with BlueBox app (app available in this repo : https://github.com/bluebox-insa/bluebox-android-app)


    ![architecture](./installation/images/architecture_mvp3.jpg)

## Run from a fresh Raspberry install 🐍
```bash
# install bluebox server and bluetool
git clone https://github.com/bluebox-insa/bluebox.git
cd bluebox && sudo make install
git clone https://github.com/bluebox-insa/bluetool.git
cd bluetool && sudo make install

# to configure and launch the server, please reboot
sudo reboot now
```
## Comments 
- To configure the raspberry using bluebox app (https://github.com/bluebox-insa/bluebox-android-app), the smartphone and the raspberry must be connected on the same network. Please check ip address of your raspberry (same as flask server).
