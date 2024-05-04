djenius
=======

A collaborative jukebox tailored for LAN environments. This project features:

* fully offline web client
* generic music source/resolver API, with Spotify & YouTube readily available
* generic auth backend, typically useful in an SSO environment
* good performances for ~thousands of songs and ~200 clients connected simultaneously
* role mappings for various actions:

  * controlling the radio: pause, seek, skip, volume
  * moderating the song queue: accept requests, ban songs, promote songs
  * voting for songs

Backend
   Python 3, aiohttp

Frontend
   React

Music renderer
   mpv

Resolvers (music sources)
   * Spotify
   * YouTube

Architecture
------------

.. code-block::

                                                +---------+
                       +--------------+---------+   mpv   |
                       |              |         +---------+
                       |              |
                  +----+----+    +----+----+    +---------+
                  +   app   +----+  nginx  +----+ browser |
                  +---------+    +--+--+---+    +---------+
                                    |  |
                                    |  |  +---------+
                  +---------+       |  |  |  media  |
    Internet +----+resolvers+-------+  +--+  cache  |
                  +---------+             +---------+

app
   Main app backend HTTP and WebSockets server. Accessible to users.

resolvers
   An HTTP server to query the various resolvers. Internal.

nginx
   Production web server. Serves static assets (``index.html`` and JS bundle), proxies backends.

media cache (part of nginx)
   Nginx built-in cache for storing static, large, costly payloads coming from the resolvers:

   * search results
   * songs
   * song cover arts

mpv
   Media player, renders the music to an audio output. Remote-controlled by the app. Reads songs from nginx cache through HTTP.

All components communicate over HTTP and can therefore be installed on separate machines.

Life of a request
~~~~~~~~~~~~~~~~~

#. user searches for "*la purée*"
#. the app dispatches the request to the resolver server (one request per resolver)
#. each resolver retrieves search results from the Internet, then the resolver server responds the JSON-encoded results back to the app
#. the app filters and populates the results (votes, play count, etc.) and forwards them to the user frontend
#. the user upvotes *Salut C'est Cool — La purée* from the Spotify resolver, enqueuing it in the playlist
#. at some point the song earns enough votes and becomes #1, so the app tells mpv to play its URL
#. mpv requests the URL, which is not cached yet, so nginx makes a request to the resolver server
#. the resolver actually downloads the Spotify song bytes from the Internet and streams them to nginx, which caches them on the way
#. nginx forwards the song bytes to mpv, which finally outputs the music to the machine sound interface

Note that each component streams bytes around, so that mpv receives bytes as they arrive from the resolver. This is important because resolvers can take seconds to minutes to retrieve the full song payload.

Both search results and song payloads are cached by nginx, ensuring a snappy user experience.

Supported resolvers
-------------------

Spotify
   uses ``despotify``[#]_, a program that is able to retrieve and decrypt Spotify audio files

YouTube
   uses the ``youtube-dl`` program to retrieve songs

.. [#] Sorry, ``despotify`` is not distributed with djenius.

Authentication
--------------

Authentication is handled by a user-provided backend that translates an HTTP request to a user-id, and a user-id to a
user. A user is an identifier (username) and a set of capabilities, such as "UpVote", "Ban", "Search", "Volume".

Setup
-----

For development, requirements are:

* Python 3.8+, virtualenv with ``requirements.txt`` and ``requirements-dev.txt`` (for testing)
* Docker and docker-compose with ``devel/docker-compose.yml``, which takes care of spawning nginx with its cache.
* Node and yarn. Use ``cd frontend && yarn install`` to bootstrap the frontend.

For production, requirements are:

* Python 3.8+, virtualenv with ``requirements.txt``
* nginx with a configuration similar to ``devel/nginx.conf``

Running in development
----------------------

The development environment is entirely built on docker compose.

Hot-reload is supported for the frontend.

Any change to djenius backend/resolver code will need a rebuild of the
containers.

1. Go to the `devel` directory::

    $ cd devel

2. Up the docker compose::

    $ docker compose -p djenius up --build

You may add `-d` to the command to run in detached mode.
Once up, the website should be accessible at `localhost:80`.

Running tests
-------------

Use pytest::

   $ PYTHONPATH=.:djenius-base pytest test/

Distributing
------------

1. Build optimized frontend bundle::

    $ (cd frontend && npm run build )

1. Build the Python sdist, which bundles the frontend assets::

    $ ( cd djenius-base && python setup.py sdist )
    $ python setup.py sdist

Point the web server to the static files at ``<env-root>/djenius/www``.
