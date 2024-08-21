This is the top-level README for the Brace project, not to be confused with the readme in the [book](book/README.md) folder.


Look at `compose.yaml` for some Docker Compose deployment details.

Useful commands:
 - `sudo docker compose up -d`
 - `sudo docker compose down`
 - `sudo docker compose logs -f`

Todo:
- write up requirements
    - VM system requirements
    - OpenAI access key
- writeup deployment process
    - VM provisioning
    - system configuration outside of docker
    - system configuration inside of OWUI
        - recommended admin settings
        - how to install our filters and stuff
- writeup knowledge update process
    - explain how knowledge is communicated through the filesystem via `/book`
    - recommend gitbook (preferred, but expensive for >1 user)
    - gh codespaces as good and cheap fallback for group