# Sucket

A tool to download all objects from an S3 bucket. Supports filtering keys by a prefix.

## Help

```
-> % sucket --help
Usage: sucket [OPTIONS] BUCKET_NAME [PREFIX]

  Download all files from a S3 bucket

  Everything from the bucket BUCKET_NAME is downloaded, with an optional key
  filter, specified with PREFIX

  By default the "folder" mode is used, which will keep the bucket "folder
  structure" when downloading.

  The "flat" mode will download all objects into the current folder by
  adding the folder structure into the key name.

  The "keys-only" will completely disregard the folders and put all files in
  the current folder.

Options:
  -m, --mode [folder|flat|keys-only]
                                  The structure to download the objects in.
  -y, --yes                       Don't prompt for continuing
  -q, --quiet                     Don't print out any info, assumes --yes
  -s, --semaphores INTEGER        Max number of asynchronous requests to make.
                                  Default: 1000
  --help                          Show this message and exit.
```

## Examples

![folder](https://raw.githubusercontent.com/ikornaselur/sucket/master/.github/examples/folder.png)
![flat](https://raw.githubusercontent.com/ikornaselur/sucket/master/.github/examples/flat.png)
![keys-only](https://raw.githubusercontent.com/ikornaselur/sucket/master/.github/examples/keys-only.png)

## Notes

This has only been tested on a fairly limited set of data, but has worked well
for ~3500 small files. Need to tweak and experiment with larger files.

# Special thanks

This is heavily based on a script that [@steinnes](https://github.com/steinnes) wrote some time ago and has
been very useful to me for a long time, the name was entirely his idea.
