# Portfolio

<div align="center">

![Portfolio](https://github.projectnova.download/public/projects/portfolio.svg)

</div>

The site that shows the rest of these projects.

This is where the work is presented: what each project is, what it does, and a link to see it
running. It is also the entry point that explains the ecosystem as a whole rather than leaving a
visitor to piece it together from separate repositories.

## What it does

- **A page per project.** Each one gets a description written for a reader who is not already
  familiar with it, with the live demo and the repository linked.
- **One consistent presentation.** Projects share a layout and a visual language, so the collection
  reads as one body of work rather than a set of unrelated pages.
- **A resume that stays current.** The resume is rendered from the same source as the rest of the
  site, so it cannot drift out of date the way a PDF upload inevitably does.
- **Behind the same gate as everything else.** The portfolio is protected by GateKeeper, like the
  projects it links to.

## Running it

```bash
cp .env.example .env
# then fill in the values it documents, and start the stack
docker compose up -d --build
```

`.env.example` lists every variable. The site is served through Caddy on the local port named there.

## Adding a project

Add an entry to the `PROJECTS` dictionary in `apps/data.py`, with the description, the
demo link, and the repository link. The layout is shared, so a new entry needs no template work.

## Documentation

Full documentation is served by the stack at `/documentation/`, and the sources are in
[`documentation/docs`](documentation/docs).
