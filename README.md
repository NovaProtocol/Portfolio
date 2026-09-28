# Portfolio

<div align="center">

![Portfolio](https://github.projectnova.download/public/project/portfolio.svg)

</div>

The site that shows the rest of these projects.

This is where the work is presented: what each project is, what it does, and a link to see it running.
It is also the entry point that explains the ecosystem as a whole, rather than leaving a visitor to
piece it together from separate repositories.

A recruiter or a collaborator should be able to land here, understand what has been built, and reach
any of it in one click.

## What it does

**A page per project.** Each one gets a description written for a reader who is not already familiar
with it, alongside the live demo and the repository. The description is about what the project does
and why it exists, not a list of the technology used to build it.

**One consistent presentation.** Projects share a layout and a visual language, so the collection
reads as one body of work instead of a set of unrelated pages. The animated badge on each project
comes from the same asset server that serves the profile graphics.

**A resume that stays current.** The resume is rendered from the same source as the rest of the site,
so it cannot drift out of date the way an uploaded PDF inevitably does. Editing the data updates both
the on-screen view and the printable version.

**Named resumes over one source.** `data/default_resume.json` is the resume, and
it is the generic one: the version to bring to a job fair where you do not know
who is reading. `data/overwrite_resume.json` lists named resumes, each carrying
only what it changes — a headline, a summary, and the projects worth leading
with. Everything else is inherited, so the two cannot disagree and a project is
written once no matter how many resumes show it.

**Behind the same gate as everything else.** The portfolio is protected by GateKeeper, like the
projects it links to. The resume in particular carries personal details, so it is exactly the kind of
page that should sit behind a login rather than being world-readable.

## Running it

```bash
# env comes from the shell — there is no .env file (see .env.example for the list)
export DEPLOYMENT_TYPE=DEBUG
docker compose up -d --build
```

The site is served through Caddy on the local port named in `.env.example`.

## Adding a project

Add an entry to the `PROJECTS` dictionary in `apps/data.py` with the description, the demo link, and
the repository link. The layout is shared, so a new entry needs no template work.

## Documentation

Full documentation is served by the stack at `/documentation/`, and the sources are in
[`documentation/docs`](documentation/docs).
