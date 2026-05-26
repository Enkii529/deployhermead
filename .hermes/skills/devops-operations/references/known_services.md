# Known Services in Hermes/OpenClaw

| Service                    | Port/Process                        | Notes                                  |
|---------------------------|-------------------------------------|----------------------------------------|
| n8n                       | 5678 (HTTP)                         | accessible at http://localhost:5678   |
| Hermes Gateway            | Python process (`hermes gateway`)   | main agent                             |
| Brain Command Center      | 8787 (HTTP)                         | Python Flask app from Brain/command_center_panel |
| Enki Browser (NAN?)       | 4318 (HTTP)                         | Node.js server.js from hermes-command-center/tools/enki-browser-2 |
| Brain API (Windows host)  | 8090 (HTTP) on 192.168.56.1        | runs via Docker compose on Windows    |
