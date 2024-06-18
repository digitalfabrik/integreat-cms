{
  inputs = {
    utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, utils }:
    utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        pg-start = pkgs.writeShellApplication {
          name = "pg-start";
          runtimeInputs = [ pkgs.postgresql ];
          text = ''
            if test ! -d "$PGDATA"; then
                pg-reset
            fi
            if ! pg_ctl status 2>/dev/null | grep -q "server is running"; then
                pg_ctl start \
                    -l "$PGLOG" \
                    -o "-c unix_socket_directories=$PGDIR -F -p $INTEGREAT_CMS_DB_PORT -k $PGLOCK"
            fi
          '';
        };
        pg-stop = pkgs.writeShellApplication {
          name = "pg-stop";
          runtimeInputs = [ pkgs.postgresql ];
          text = ''
            if pg_ctl status 2>/dev/null | grep -q "server is running"; then
              pg_ctl stop
            fi
          '';
        };
        pg-reset = pkgs.writeShellApplication {
          name = "pg-reset";
          runtimeInputs = [ pkgs.postgresql pg-start pg-stop ];
          text = ''
            pg-stop

            if test ! -d "$PGDIR"; then
                mkdir "$PGDIR"
                mkdir "$PGLOCK"
            fi
            rm -rf "$PGDATA"

            initdb "$PGDATA" --auth=trust -U "$INTEGREAT_CMS_DB_USER" >/dev/null

            pg-start
            createdb -h "$INTEGREAT_CMS_DB_HOST" -p "$INTEGREAT_CMS_DB_PORT" -U "$INTEGREAT_CMS_DB_USER" "$INTEGREAT_CMS_DB_NAME"
          '';
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python311Full
            python311Packages.pip
            python311Packages.platformdirs

            nodePackages.npm
            nodejs_21

            gettext
            netcat-gnu
            pcre16
            file
            gnused
            glibcLocales
            stdenv.cc.cc.lib
          ] ++ [
            pg-start
            pg-stop
            pg-reset
          ];

          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib pkgs.file ];

          shellHook = /* bash */ ''
            set_if_unset() {
                if [ -z "$(eval \$$1)" ]; then
                    export "$1"="$2"
                fi
            }

            set_if_unset PGDIR "$(pwd)/.postgres"
            set_if_unset PGDATA "$PGDIR/data"
            set_if_unset PGLOG "$PGDIR/log"
            set_if_unset PGLOCK "$PGDIR/lock"

            set_if_unset INTEGREAT_CMS_DB_NAME "integreat"
            set_if_unset INTEGREAT_CMS_DB_USER "integreat"
            set_if_unset INTEGREAT_CMS_DB_PASSWORD "password"
            set_if_unset INTEGREAT_CMS_DB_HOST "localhost"
            set_if_unset INTEGREAT_CMS_DB_PORT "5432"

            # These are set in the devtools at appropriate locations;
            # additionally setting them here allows for testing integration in code editors
            set_if_unset DJANGO_SETTINGS_MODULE "integreat_cms.core.settings"
            set_if_unset INTEGREAT_CMS_DEBUG 1
            set_if_unset INTEGREAT_CMS_DEEPL_AUTH_KEY "dummy"
            set_if_unset INTEGREAT_CMS_FCM_CREDENTIALS "dummy"
            set_if_unset INTEGREAT_CMS_SECRET_KEY "dummy"
            set_if_unset INTEGREAT_CMS_BACKGROUND_TASKS_ENABLED 0
            set_if_unset INTEGREAT_CMS_SUMM_AI_API_KEY "dummy"
            set_if_unset INTEGREAT_CMS_LINKCHECK_DISABLE_LISTENERS 1

            # Setting LD_LIBRARY_PATH can cause issues on non-NixOS systems
            if ! command -v nixos-version &> /dev/null; then
                unset LD_LIBRARY_PATH
            fi

            SOURCE_DATE_EPOCH=$(date +%s)
            VENV=.venv
            if [ -d $VENV ]; then
              source ./$VENV/bin/activate
            fi
            export PYTHONPATH=`pwd`/$VENV/${pkgs.python311Full.sitePackages}/:$PYTHONPATH
          '';
        };
      });
}
