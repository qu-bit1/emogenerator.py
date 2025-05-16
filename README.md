#### APPLE MUSIC PLEASE LEARN SMTH FROM SPOTIFY
# emogenerator.py

## why this exists

- because good taste deserves automation.
- because you shouldn’t have to drag tracks one by one.
- because text is enough.(and if you talk to gpt as your friend and someday it wrote you a list of potential good songs for you as your best friend)


---

## what it does

`emogenerator.py` reads plain text files that look like this:

```
Name: sagar-core vol. 2 – softboy renaissance
fade into you --- mazzy star
coffee --- beabadoobee
line without a hook --- ricky montgomery
```

it creates a playlist on your spotify account with the exact tracks.
matches your saved songs first.
creates multiple playlists at once.
requires no spotify dashboard tinkering—auth handled in-script.

---

## setup

1. clone the repo

2. copy the config template

   ```bash
   cp config/template.ini config/config.ini
   ```

3. add your spotify client id + secret

4. run the token script

   ```bash
   python get_token.py
   ```

   it will open a browser, you approve, it saves the access token and your user id.(so no need to get access token every now and then, automatically refreshes it)

5. drop your `.txt` playlists into the `playlists/` folder

6. run

   ```bash
   python app.py
   ```

---

## format

each `.txt` file should follow this:

```
Name: [playlist name]
Track Name --- Artist Name
Track Name --- Artist Name
...
```

you can change the delimiter in `config.ini` (`---`, `-`, `|`, etc.)

---

## example

`playlists/playlist-02.txt`

```
Name: sagar-core vol. 2 – softboy renaissance
we might be dead by tomorrow --- soko
frisk --- black marble
anchor --- novo amor
```

one run later → a real spotify playlist under your name.

---

## todo
- [ ] add mood-tagging with the ultimate power of nlp
