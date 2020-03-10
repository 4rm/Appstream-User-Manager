<img src="https://i.imgur.com/Ht86JYX.png" alt="Logo" width=450>

GUI alternative to managing Appstream users
<p align="center">
<img src="https://thumbs.gfycat.com/UnkemptSerpentineKiwi-size_restricted.gif" height=400 alt="screenshot">
</p>

<table>
<tr><td><ul>
<b><p align="center">Contents</p></b>
<li><a href="#Tech">Technology used</a></li>
<li><a href="#How">How it works</a></li>
  <ul><li><a href="#GettingStart">Getting Started</a></li>
    <li><a href="#Usage">Usage</a></li>
    <ul><li><a href="#Manage">Manage</a></li>
      <li><a href="Add">Add</a></li>
    <li><a href="Remove">Remove</a></li></ul>
  </ul>
<li><a href="#Known">Known Issues</a></li>
<li><a href="#Future">Future Improvements</a></li>
</ul></td></tr>
</table>

## <a name="Tech">Technology used</a>

<table>
  <tr>
  <td><a href="https://github.com/exhuma/puresnmp">Boto 3</a> (1.10.46) </td>
    <td>AWS SDK for Python </td><tr>
    <td><a href="https://pypi.org/project/keyring/">Keyring</a> (18.0.0)</td>
  <td>Communicating with native OS keychain</td></tr><tr>
  <td><a href="https://pandas.pydata.org/">Pandas</a> (1.0.1)</td>
  <td>Data analysis tool</td>
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

There are three main windows in the Appstream User Manager: Manage, Add, and Remove

#### <a name="Manage">Manage</a>
<p align="center">
<img src="https://i.imgur.com/kIVomoj.png" alt="Manage tab" width=600>
</p>

From the Manage tab, you can search for users via first or last name, or email address. When a user is selected, they will appear in the User Info Pane, which will tell you what stacks are associated with said user. You also have the option of resending a welcome email the user hasn't yet registered a password (temp passwords from account creation emails expire after 7 days).

You also have the option of Setting, Adding, or Removing stacks from the user's account. "Setting" the stacks means checked stacks will be added, and unchecked stacks will be removed. "Adding" will just add selected stacks, and "Removing" will just remove selected stacks. You also have the option of sending a notification email.

<p align="center">
  <img src="https://i.imgur.com/1hFIvFd.png" alt="Set example" width=400>
  <br>
  <i>What you'll see when "Setting" stacks</i>
</p>

#### <a name="Add">Add</a>
<p align="center">
<img src="https://i.imgur.com/p4N2k0J.png" alt="Add tab" width=600>
</p>

From the Add tab, users can be added individually or by roster. Adding by roster requires the standard Rutgers REGIS format. The file must also be formatted as `.csv`

REGIS-formatted rosters saved as `.xlsx` can be `save[d] as .csv` in excel and should work fine.

<p align="center">
  <img src="https://i.imgur.com/Yp12m7P.png" alt="roster example" width=400>
  <br>
  <i>Standard REGIS .csv</i>
</p>

Selected stacks will be associated with the added users, whether by roster or individual addition. Please note that usernames are case-sensitive.

#### <a name="Remove">Remove</a>
<p align="center">
<img src="https://i.imgur.com/KDSEv4u.png" alt="Remove tab" width=600>
</p>

From the Remove tab, specific users can be removed using Batch Remove, or the entire user list can be deleted (with exceptions) from Remove All. User accounts cannot be recovered, but their data should remain in their S3 bucket.
                                                                     
## <a name="Known">Known Issues</a>
* Rate limiting happens <i>a lot</i>. Had to add delays all over the place.

## <a name="Future">Future Improvements</a>
* Add user count
* Adding-users-with-stacks needs to consider that some users may already exist
* Search by stack association
