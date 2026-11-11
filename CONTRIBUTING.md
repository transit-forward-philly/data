# Contributing

Thanks for helping out. There are a few ways to get involved, and you don't need to code for most of them.

## Ways to help

- **Data curation:** find sources, clean spreadsheets, write data dictionaries, check numbers.
- **Pipelines:** write or maintain scripts that pull and refresh public data.
- **Analysis and reporting:** turn data into findings, charts, and short write-ups.

Open tasks and data requests live in [Issues](../../issues). Pick one up, or open a new one.

## The one standard: sourcing

Use whatever tools you're comfortable with. What matters is that someone else can check your work:

1. **Say where the data came from.** A link to the original source, and the date you pulled it.
2. **Say what you did to it.** Filtering, joining, cleaning. A few sentences is fine.
3. **Describe the columns.** Use the template in [`docs/dataset-template.md`](docs/dataset-template.md).

## Contributing without a pull request

Pull requests are one way in, not the only one. All of these are welcome, and you get credit either way:

- **Send code or data another way.** Attach a file or paste a snippet in an [Issue](../../issues), share a gist, or send it to a maintainer. Someone will commit it with you credited as co-author.
- **Keep your own repo.** Build a pipeline or tool in a repository you control, under your own rules. We'll link to it from here or use its output files, and your code never has to touch this repo.
- **Review.** Reviewing pull requests, especially scripts and anything that runs code, is one of the most valuable things you can do. See [SECURITY.md](SECURITY.md) for what we check.

## Practical notes

- Keep raw files that are very large (GTFS feeds, map extracts) out of the repo. Write down how to download them, or add a script in `pipelines/`.
- Use plain formats: CSV for tables, GeoJSON for maps.
- New to GitHub? Ask in an issue and someone will walk you through it. You can also upload files right from the GitHub website.
