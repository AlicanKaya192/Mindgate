---
name: expert-docker
description: Docker and container expertise pack. Load when working on a Dockerfile, docker compose, image size or security, container networking, a volume, or a development environment running in a container.
---

Expertise pack (not an agent). Read whether Docker is installed and which projects use it from the environment note in the vault (`me/environment.md`) and the project notes.

## Checklist
- [ ] The base image is official and **version-pinned** (`python:3.12-slim`, not `latest`); small if possible (slim, alpine: check compatibility).
- [ ] Multi-stage build: build tools are not in the final image.
- [ ] Non-root user (`USER`); no needless privilege (`--privileged`).
- [ ] A `.dockerignore` exists: `.git`, `.env`, `node_modules`, local data do not enter the image.
- [ ] Secrets are not baked into the image (via ENV or COPY); they are supplied at run time.
- [ ] Layer order suits the cache (dependency file first, then code).
- [ ] Health check (`HEALTHCHECK`), clean shutdown, one-process principle.
- [ ] Compose: only the necessary ports, and another port if one is taken (#20); named volumes; separate networks.
- [ ] Image scan (`docker scout` or `trivy`; if not installed, ask the user).

## Hard rules
- **Deletion commands** such as `docker system prune`, `docker volume rm` and `docker rmi` only with the user's permission (#22); explain which image or volume will be deleted and why.
- Do not stop or close someone else's container or Docker Desktop.

## Verification
- Show the output of `docker build` and `docker run`; measure the image size (#24).

## Additional methods
Ideas are in our own words.
- **Compose and runtime hardening:**
  - [ ] No `privileged: true`, `network_mode: host` or mounting `/var/run/docker.sock`. These give the container full authority on the host; if needed, ask the user with the reason.
  - [ ] If ports are opened only locally, in the form `127.0.0.1:<port>:<port>`.
  - [ ] If possible `read_only: true`, `cap_drop: [ALL]` (add back what is needed), `security_opt: [no-new-privileges:true]`.
  - [ ] Resource limits (memory, CPU) are defined.
- **Pinning:** In production, prefer a digest (`@sha256:…`) to an image tag.
- **Kubernetes** (if needed): `resources` limits, `readinessProbe`/`livenessProbe`, `securityContext.runAsNonRoot: true`, secrets in a Secret object (not plain in git).
- Idea sources: semgrep/skills (`code-security`: Docker/Kubernetes checks), VoltAgent (`docker-expert`, `kubernetes-specialist`).

## Lessons
<!-- The central agent adds verified lessons here: general and reusable, without project names or dates. -->
- In a packaged app, try the Docker exercises separately in the packaged build.
