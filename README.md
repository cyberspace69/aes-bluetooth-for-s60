# AES Bluetooth for s60

## About

This project provides a working example of transmitting and receiving encrypted (AES-256 in CTR mode) information from a device running Symbian s60 wirelessly via bluetooth.

Two examples of sending / receiving information are included:

- Sending encrypted messages (not SMS) on a Symbian s60 device to a server
- Server responding to the client with an encrypted JSON to parse

## How It Works

Both the client and server scripts contain a keyphrase. This keyphrase is then used to encrypt / decrypt messages.

In the project, the *placeholder* keyphrase on both the client and server is the same and can run as-is. Be sure to change this!

When running the client script on an s60 device, a box will appear asking for user input, which later goes through a packing process of:

- Taking the input
- Encrypting input with the provided keyphrase via AES-256 in CTR mode
- Wrapping the encrypted message via base64 encoding

Once packed, the message is sent via bluetooth to a receipient who goes through the process in reverse (unwrap, decrypt, etc).

## Prerequisites

To run the client, you must have a device compatible with Nokia's [Python for s60](https://web.archive.org/web/20081217180059/http://www.forum.nokia.com/Resources_and_Information/Tools/Runtimes/Python_for_S60/), a port of the Python programming language to s60 devices.

This project contains a client script compatible with Python 2.5.4 (supported in **Python for s60 version 1.9.3+**), as well as a server script compatible with  Python 3.8.

The server can be run on any device running Python 3.8 or higher. Of course, the device will need the ability to transmit / receive over bluetooth as well.

**Please note:** While bluetooth today is a common feature of most devices, be sure it's available on your chosen Symbian s60 device!

## Dependencies

- [pyaes](https://github.com/ricmoo/pyaes), a pure-python implementation of AES256 encryption

## Installation

To load the script onto the s60 device, the easiest method is to connect and transfer the files via bluetooth.

On the s60 device, add the **blu_client.py** script under **C:/Data/python**

![py_script](https://user-images.githubusercontent.com/69375951/128249555-cb117ada-97cf-4e79-af79-761b6ec1a2af.png)

To install the additional dependencies, create a folder called **lib** within the **python** directory. From here, add the files.

![dirrr](https://user-images.githubusercontent.com/69375951/128249756-ed6d3f05-3434-42da-a4a4-ba9c186ddc1f.png)

**Note** - you may need to create the folders manually.

For the server code, the only external dependency is **pyaes**, which can be imported directly within the project.

## Running the script

To run the scripts, make sure bluetooth is enabled on both the client and server. For the s60 client, this is managed under the **Connectivity** options.

First run the server script. You can do this by entering the **server** project directory via terminal and running:

```
python blu_ser.py
```

Once the server is running you can start the client.

Simply open your Python app under **Installations** on your s60 device, select **Options**, then **Run script**.

From here, you should see the scripts available within the **python** directory of the device. Select **blu_client.py**, which will begin searching for bluetooth connections.

Once your server is found, you'll be prompted to connect, followed by a prompt to enter text. This is later encrypted / wrapped then sent to the server.

## Additional Resources

### Finding Supported Devices

A list of mobile phones compatible with various version of Python for s60 [can be found here](https://en.wikipedia.org/wiki/S60_(software_platform)).

To check the available features of each phone, please refer to: https://www.gsmarena.com/

Using the [Nokia E71](https://www.gsmarena.com/nokia_e71-2425.php) as an example below, you can see this device includes WiFi and GPS in addition to bluetooth.

![nokia_e71](https://user-images.githubusercontent.com/69375951/128099832-b44e20ff-5059-4477-802b-e29042939a5e.png)

### s60 Python Examples

There's quite a few good resources for learning about Python for s60's included modules, as well as writing custom ones.

For Python examples specifically handling network related tasks on s60 devices, [check out this great walkthrough](http://croozeus.com/blogs/?p=525).

Also, there's a great directory of applications to reference as a starting point [available from this link](http://croozeus.com/blogs/?page_id=838).
