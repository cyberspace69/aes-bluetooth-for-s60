# Client Installation

To install, copy the **python** to a s60 device to the following path:

`
C:\Data\
`

You will end up with something like this:

![asdffjfj](https://user-images.githubusercontent.com/69375951/128440122-a54300e4-e658-464e-a9a1-a0b856675b52.png)


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
