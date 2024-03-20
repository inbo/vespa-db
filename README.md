# VespaDB: Asian Hornet Monitoring Application

## Overview

VespaDB is a Django-based application developed for the Vespa-Watch project to monitor and manage the spread of the invasive Asian Hornet (*Vespa velutina*) in Europe. As a part of the effort to protect local fauna and flora, the application enables the collection and management of sightings and eradication efforts. This application serves as a central platform for citizens to report nests, for authorized eradicators to document their actions, and for administrators to manage the data efficiently.

## Features

- **Central Database**: Stores reports of Asian Hornet nests including date, location, photos, and reporter's information.
- **External API Integration**: Automatically imports new sightings daily from an Waarnemingen.be API.
- **Bulk Import**: Supports bulk import of sightings from other sources.
- **CSV Export**: Enables export of public data to CSV format for analysis and reporting.
- **Web Application**:
  - Registration system for authorized eradicators.
  - Public online map displaying all sightings with filtering options (date, status, municipality, GIS layer).
  - Form submission for eradicators to add information about eradication efforts (date, materials used, result).
  - Admin panel for modifying and deleting reports.

## Commands

#### load_municipalities Command

This command imports municipality data from a specified Shapefile into the VespaDB database. It is essential for setting up the application's geographic features.

Usage: python manage.py load_municipalities

This command reads the Shapefile located in the `data/Refgem.shp` path relative to the script's directory, creating new municipality entries in the database. If a municipality already exists, its polygon geometry will be updated.
