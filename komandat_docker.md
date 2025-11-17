📘 Docker Quick Commands – Cheatsheet

Ky dokument përmbledh të gjitha komandat më të përdorura për Docker, Docker Compose, grupet, containerat, imazhet dhe volumet.

## 🟩 1. Konfigurimi fillestar (docker group)
➤ Krijo grupin docker (nëse nuk ekziston)
sudo groupadd docker

➤ Shto përdoruesin tek docker group
sudo usermod -aG docker $USER

➤ Rifresko grupet pa logout
newgrp docker

➤ Kontrollo nëse u shtua suksesshëm
groups $USER

➤ Testo Docker pa sudo
docker ps

## 🐳 2. Komandat kryesore të Docker
🔹 Shfaq lista e containerave
Vetëm aktivët:
docker ps

Të gjithë containerat:
docker ps -a

🔹 Start / Stop / Restart i një container-i

Start:

docker start <container_name>


Stop:

docker stop <container_name>


Restart:

docker restart <container_name>

🔹 Fshij një container
docker rm <container_name>

Fshi container të ndaluar:
docker container prune

## 🧱 3. Komandat për Docker Images
Listo imazhet:
docker images

Fshi një imazh:
docker rmi <image_id>

Fshi të gjitha imazhet e padobishme:
docker image prune -a

## 📦 4. Komandat për Volumet
Listo volumet:
docker volume ls

Fshi një volum:
docker volume rm <volume_name>

Fshi të gjitha volumet e padobishme:
docker volume prune

## 🗂️ 5. Docker Compose (versioni modern)

Start (foreground – shfaq logs):

docker compose up


Start me rebuild:

docker compose up --build


Start në background:

docker compose up -d


Stop:

docker compose down


Stop + fshi voluma:

docker compose down -v


Stop + fshi imazhet e build-imit:

docker compose down --rmi all

## 📜 6. Logs dhe debugging

Logs të një shërbimi:

docker logs <container_name>


Logs në live (tail):

docker logs -f <container_name>


Shiko hapësirën e marrë nga docker:

docker system df


Pastro gjithçka e padobishme:

docker system prune -a

## 🚨 7. Troubleshooting të zakonshëm
❗ “permission denied” kur përdor docker
sudo usermod -aG docker $USER
newgrp docker

❗ docker: command not found

Instalo docker:

sudo apt update
sudo apt install docker.io

❗ docker compose: command not found

Instalo:

sudo apt install docker-compose-plugin

## 🟩 8. Shkurtesa për zhvillim
Start i shpejtë
docker compose down -v
docker compose up --build

Fshi gjithçka dhe nise nga zero
docker system prune -a --volumes