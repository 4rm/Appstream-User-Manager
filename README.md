<img src="https://i.imgur.com/Ht86JYX.png" alt="Logo" width=450>

GUI alternative to managing Appstream users \#UNDER CONSTRUCTION\#

<img src="https://i.imgur.com/eeLyia7.jpg" alt="screenshot">

<table>
<tr><td><ul>
<b><p align="center">Contents</p></b>
<li><a href="#Tech">Technology used</a></li>
<li><a href="#How">How it works</a></li>
  <ul><li><a href="#GettingStart">Getting Started</a></li>
    <li><a href="#Usage">Usage</a></li>
  </ul>
<li><a href="#Known">Known Issues</a></li>
<li><a href="#Future">Future Improvements</a></li>
</ul></td></tr>
</table>

## <a name="Tech">Technology used</a>

<table>
  <tr>
  <td><a href="https://github.com/exhuma/puresnmp">Boto 3</a> (1.10.46) </td>
    <td>AWS SDK for Python </td>
  </tr>
</table>

## <a name="How">How it works</a>

### <a name="GettingStart">Getting Started</a>

In order to use the Appstream User Manager, you'll need an Access Key ID and a Secret Access Key. To obtain one, log in to the AWS console and go to "My Security Credentials" under the user account dropdown menu.
<p align="center">
<img src="https://i.imgur.com/GnRz9te.png" alt="user account dropdown menu" height=300 align="center">
</p>
Then, create an access key under "Access keys for CLI, SDK, & API access". Note that you can only generate a total of 2 Access keys (unless you have been provisioned more by an administrator).

&nbsp;

<p align="center">
<img src="https://i.imgur.com/nlV2LS0.png" alt="Access keys generation section" width=500>
</p>

&nbsp;

Once your Access key has been made, you will be able to view your Secret Access Key. THIS IS THE ONLY TIME YOU WILL BE ABLE TO VIEW IT. Make sure you make a copy of your key somewhere secure, or else you'll have to recreate your access keys.

<p align="center">
<img src="https://i.imgur.com/HXYLCfL.png" alt="Secret key viewing window" width=300>
</p>

### <a name="Usage">Usage</a>

There are three main windows in the Appstream User Manager: Manage, add, remove

## <a name="Known">Known Issues</a>
* Rate limiting happens <i>a lot</i>. Had to add delays all over the place.

## <a name="Future">Future Improvements</a>
* General beautification (add icons, etc)
