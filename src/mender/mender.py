# Copyright 2021 Northern.tech AS
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
import argparse
import logging as log
import sys

import mender.bootstrap.bootstrap as bootstrap
import mender.client.authorize as authorize
import mender.client.deployments as deployments
import mender.settings.settings as settings
import mender.statemachine.statemachine as statemachine

from mender.log.log import DeploymentLogHandler


def run_daemon(args):
    log.info("Running daemon...")
    statemachine.run(force_bootstrap=args.forcebootstrap)


def show_artifact(_):
    log.info("Currently installed Artifact: ")
    try:
        with open(settings.PATHS.artifact_info) as f:
            data = f.read()
            log.info(data)
    except FileNotFoundError:
        log.error(f"No device_type file found in {settings.PATHS.data_store}")


def run_bootstrap(args):
    log.info("Bootstrapping...")
    bootstrap.now(
        private_key_path=settings.PATHS.key, force_bootstrap=args.forcebootstrap
    )


def run_version(_):
    print("version: alpha")


def report(args):
    context = statemachine.Context()
    context = statemachine.Init().run(context)
    jwt = authorize.request(
        context.config.ServerURL,
        context.config.TenantToken,
        context.identity_data,
        context.private_key,
        context.config.ServerCertificate,
    )
    if not jwt:
        log.error("Failed to authorize with the Mender server")
        sys.exit(1)
    try:
        with open(settings.PATHS.lockfile_path) as f:
            deployment_id = f.read()
            if not deployment_id:
                log.error("No deployment ID found in the lockfile")
                sys.exit(1)
    except FileNotFoundError:
        log.error("No update in progress...")
        sys.exit(1)
    if args.success:
        log.info("Reporting a successful update to the Mender server")
        if not deployments.report(
            context.config.ServerURL,
            deployments.STATUS_SUCCESS,
            deployment_id,
            context.config.ServerCertificate,
            jwt,
            deployment_logger=None,
        ):
            log.error("Failed to report the update status to the Mender server")
            sys.exit(1)
    elif args.failure:
        log.info("Reporting a failed update to the Mender server")
        update_handlers = [
            handler
            for handler in log.getLogger("").handlers
            if isinstance(handler, DeploymentLogHandler)
        ]
        assert (
            len(update_handlers) == 1
        ), "Something is wrong with the setup of the DeploymentLogHandler"
        deployment_log_handler = update_handlers[0]
        deployment_log_handler.enable()
        if not deployments.report(
            context.config.ServerURL,
            deployments.STATUS_FAILURE,
            deployment_id,
            context.config.ServerCertificate,
            jwt,
            deployment_log_handler,
        ):
            log.error("Failed to report the update status to the Mender server")
            sys.exit(1)
    else:
        log.error("No report status given")
        sys.exit(1)


def setup_log(args):
    level = {
        "debug": log.DEBUG,
        "info": log.INFO,
        "warning": log.WARNING,
        "error": log.ERROR,
        "critical": log.CRITICAL,
    }.get(args.log_level, "info")
    handlers = []
    handlers.append(log.StreamHandler())
    # TODO - setup this for the device, see:
    # https://docs.python.org/3/library/logging.handlers.html#sysloghandler
    syslogger = log.NullHandler() if args.no_syslog else log.handlers.SysLogHandler()
    handlers.append(syslogger)
    if args.log_file:
        handlers.append(log.FileHandler(args.log_file))
    deployment_log_handler = DeploymentLogHandler()
    handlers.append(deployment_log_handler)
    root_logger = log.getLogger("")
    root_logger.setLevel(level)
    for handler in handlers:
        root_logger.addHandler(handler)
    log.info(f"Log level set to {args.log_level}")


def main():
    parser = argparse.ArgumentParser(
        prog="mender",
        description="""mender
    integrates both the mender daemon and commands for manually performing
    tasks performed by the daemon (see list of COMMANDS below).""",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    #
    # Commands
    #
    subcommand_parser = parser.add_subparsers(title="COMMANDS")
    bootstrap_parser = subcommand_parser.add_parser(
        "bootstrap", help="Perform bootstrap and exit."
    )
    bootstrap_parser.set_defaults(func=run_bootstrap)
    daemon_parser = subcommand_parser.add_parser(
        "daemon", help="Start the client as a background service."
    )
    daemon_parser.set_defaults(func=run_daemon)
    show_artifact_parser = subcommand_parser.add_parser(
        "show-artifact",
        help="Print the current Artifact name to the command line and exit.",
    )
    show_artifact_parser.set_defaults(func=show_artifact)
    report_parser = subcommand_parser.add_parser(
        "report", help="Report the update status",
    )
    report_parser.set_defaults(func=report)
    report_parser.add_argument(
        "--success",
        help="Report a succesful update to the Mender server",
        default=False,
        action="store_true",
    )
    report_parser.add_argument(
        "--failure",
        help="Report a failed update to the Mender server",
        default=False,
        action="store_true",
    )
    #
    # Options
    #
    global_options = parser.add_argument_group("Global Options")
    global_options.add_argument(
        "--data",
        "-d",
        help="Mender state data DIRECTORY path.",
        default="/var/lib/mender",
    )
    #
    # Logging setup
    #
    global_options.add_argument(
        "--log-file", "-L", help="FILE to log to.", metavar="FILE"
    )
    global_options.add_argument(
        "--log-level", "-l", help="Set logging to level.", default="info"
    )
    global_options.add_argument(
        "--forcebootstrap",
        "-F",
        help="Force bootstrap.",
        default=False,
        action="store_true",
    )
    global_options.add_argument(
        "--no-syslog",
        help="Disble logging to syslog.",
        default=False,
        action="store_true",
    )
    global_options.add_argument(
        "--version", "-v", help="print the version", default=False, action="store_true"
    )
    args = parser.parse_args()
    log.basicConfig(
        datefmt="%Y-%m-%d %H:%M:%S", format="%(asctime)s %(levelname)-8s %(message)s",
    )
    if args.version:
        run_version(args)
        return
    if args.data:
        log.info(f"Data store set to: {args.data}")
        settings.PATHS = settings.Path(data_store=args.data)
    else:
        log.info("Data store set to: '/var/lib/mender'")
        settings.PATHS = settings.Path()
    setup_log(args)
    if "func" not in vars(args):
        parser.print_usage()
        return
    args.func(args)


if __name__ == "__main__":
    main()
