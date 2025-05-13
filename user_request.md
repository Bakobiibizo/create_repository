# ComAI Client

A comprehensive tool kit for interacting with CommuneAI block chain and its services. 

## Overview

This is a tool kit for it uses RPC commands to communicate with the Commune block chain and exposes it to end users via a rich command line interface. It also provides a traditional REST API for integration with other applications. Finally it provides an MCP server for interfacing with agentic services and modules. It maintains its own database for storing user data and updates from the blockchain. The block chain its self is built on substrate and is an existing and more mature project that has been going through changes of leadership. The original cli tool is [Communex](../communex) but the developers of that project are no longer maintinging it. The development of this project is aimed at providing the tooling needed in robust and easily consumable format for the CommuneAI platform.

## Preliminary Directory Structure

- 📁 **./**
  - 📄 **README.md**
  - 📄 **main.py**
  - 📄 **pyproject.toml**
  - 📁 **src/**
    - 📁 **api/**
    - 📁 **command_line/**
    - 📁 **data_base/**
    - 📁 **context_protocol/**
    - 📁 **utililties/**
  - 📁 **tests/**
    - 📁 **api/**
    - 📁 **command_line/**
    - 📁 **data_base/**
    - 📁 **context_protocol/**
    - 📁 **utililties/**

These are the initial directories required for the project but more will be added as needed. Ensuring we keep this directory structure updated in your .ctx. files and simple for the end user is important. A flat a directory structure and full descriptive names are preferred.

## Technologies

- Python 3.12
- uv package manager for running python commands
- rich console for error handling and user display and feedback
- fast api for rest api
- substrate-interface for blockchain interaction and rpc commands
- model context protocol([MCP](../../mcp/python-sdk/)) for agentic services and modules
  - Uses SSE and StdIO transports for communication with modules. 
- sqlite for database storage
- pytest for testing
- pydantic models for data structure and validation 

## Workflow
- scafold out the project using place holder files with doc strings explaining usage
- write tests for the scafolded out files that should fail 
- implement the code running the tests to confirm that the code is functional
- code review identifying repeated code and unessiscary or unrequested complexity - particuarly
- code and security review 
- implement findings of the review
- final review 
- documentation 

## Notes

- We want to tackle this one section at a time starting with the RPC commands and the cli. Ideally it works in a similiar manner to communex but we need to pay closer attention to cli norms and best practices as well as have a stronger preference for well typed code and clear documentation.
- Commands should be grouped into clear categories based on the extrinsics and those norms should be followed in the cli, api and mcp layers consistently. 
- Query maps of the storage items should be pulled from blockchain in bulk and stored in the database.
- Those query maps should updated periodically to ensure synchronicity with the blockchain data when running in any kind of server mode. 
- The query requests should be run in a threadpool in the background to prevent blocking the main thread.
- We are focused on the cli MVP for now but we need to prepare for the rest of the application to be built on top of it and establish the norms for the rest of the application.