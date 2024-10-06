# Git Branching Strategy Guide

## Overview

This document outlines the Git branching strategy for the Cat Chat AI project. Following this strategy will help maintain a clean and organized codebase, facilitate collaboration, and streamline the development process.

## Branch Types

1. **Main Branch**: `main`
   - Always contains production-ready code
   - Protected from direct pushes

2. **Development Branch**: `develop`
   - Integration branch for features
   - Base for feature branches

3. **Feature Branches**: `feature/*`
   - Used for developing new features or enhancements
   - Branched off from and merged back into `develop`

4. **Release Branches**: `release/*`
   - Prepare for a new production release
   - Branched off from `develop`

5. **Hotfix Branches**: `hotfix/*`
   - Used to quickly patch production releases
   - Branched off from `main`

## Workflow

1. **Feature Development**:
   - Create a new feature branch from `develop`:

     ```bash
     git checkout -b feature/new-feature develop
     ```

   - Develop and commit changes
   - Push branch to remote repository
   - Create a Pull Request to merge into `develop`
   - After review and approval, merge into `develop`

2. **Preparing a Release**:
   - Create a release branch from `develop`:

     ```
     git checkout -b release/1.0.0 develop
     ```

   - Make any necessary release preparations
   - Merge release branch into `main` and `develop`:

     ```
     git checkout main
     git merge release/1.0.0
     git checkout develop
     git merge release/1.0.0
     ```

   - Tag the release in `main`:

     ```
     git tag -a v1.0.0 -m "Version 1.0.0"
     ```

3. **Hotfixes**:
   - Create a hotfix branch from `main`:

     ```
     git checkout -b hotfix/critical-bug main
     ```

   - Fix the issue and commit changes
   - Merge hotfix into `main` and `develop`:
     ```

     git checkout main
     git merge hotfix/critical-bug
     git checkout develop
     git merge hotfix/critical-bug
     ```

   - Tag the new patch version in `main`

## Best Practices

1. Keep feature branches short-lived and focused
2. Regularly pull changes from `develop` into feature branches
3. Use descriptive branch names (e.g., `feature/add-persian-cat-info`)
4. Write clear and concise commit messages
5. Delete feature branches after merging

By following this branching strategy, we can maintain a clean and organized codebase, facilitate collaboration, and streamline our development process.
