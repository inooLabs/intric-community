#!/bin/bash
# build_and_push.sh - Script for building and pushing Intric Docker images to Nexus registry
# This script follows Docker best practices for efficient building and pushing

set -e  # Exit on any error
# set -o pipefail # Optional: Exit if any command in a pipeline fails

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function for logging messages
log() {
    local level=$1
    local message=$2
    local color=$NC
    case $level in
        INFO) color=$BLUE ;;
        SUCCESS) color=$GREEN ;;
        WARN) color=$YELLOW ;;
        ERROR) color=$RED ;;
    esac
    echo -e "${color}[$level] ${message}${NC}"
}

# =====================================================
# Environment Variables and Configuration
# =====================================================

# Default values (will be used if not provided as environment variables)
DEFAULT_IMAGE_TAG="latest"
DEFAULT_NEXUS_REGISTRY="localhost:5000" # Default to local registry if not specified

# Use environment variables or defaults
NEXUS_REGISTRY=${NEXUS_REGISTRY:-$DEFAULT_NEXUS_REGISTRY}
IMAGE_TAG=${IMAGE_TAG:-$DEFAULT_IMAGE_TAG}
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# =====================================================
# Versioning Strategy Detection
# =====================================================

# Determine if we're using a Git tag as version
if [ "$IMAGE_TAG" = "latest" ]; then
    # Check if we're on a Git tag
    GIT_TAG=$(git describe --exact-match --tags 2>/dev/null || echo "")
    if [ -n "$GIT_TAG" ]; then
        log INFO "Detected Git tag: ${GIT_TAG}"
        IMAGE_TAG=$(echo "$GIT_TAG" | sed 's/^v//') # Remove leading 'v' if present
        # Check if it follows semantic versioning (X.Y.Z)
        if [[ $IMAGE_TAG =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$ ]]; then
            log SUCCESS "Using semantic version: ${IMAGE_TAG}"
        else
             log WARN "Git tag ${IMAGE_TAG} does not strictly follow SemVer X.Y.Z format, but using it anyway."
        fi
    else
        # If no specific version and not on a tag, use branch-commit format for non-main branches
        BUILD_DATE=$(date +%Y%m%d)
        if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
            # Sanitize branch name for Docker tag compatibility
            SANITIZED_BRANCH=$(echo "$CURRENT_BRANCH" | tr / - | tr -cd '[:alnum:]-')
            IMAGE_TAG="${SANITIZED_BRANCH}-${GIT_COMMIT}-${BUILD_DATE}"
            log WARN "Using development tag: ${IMAGE_TAG}"
        else
            # Keep 'latest' for main/master if no tag is present
             log INFO "Using default tag: ${IMAGE_TAG}"
        fi
    fi
fi

# =====================================================
# Parameter Validation
# =====================================================

if [ -z "$NEXUS_REGISTRY" ]; then
    log ERROR "NEXUS_REGISTRY environment variable is required"
    exit 1
fi

log INFO "Building and pushing images to: ${NEXUS_REGISTRY}"
log INFO "Using image tag: ${IMAGE_TAG}"
log INFO "Current Git Commit: ${GIT_COMMIT}"
log INFO "Current Git Branch: ${CURRENT_BRANCH}"


# =====================================================
# Registry Authentication
# =====================================================

# Login to Nexus registry if credentials are available
if [ -n "$NEXUS_USERNAME" ] && [ -n "$NEXUS_PASSWORD" ]; then
    log INFO "Attempting to log in to Nexus registry: ${NEXUS_REGISTRY} as user ${NEXUS_USERNAME}..."
    if echo "$NEXUS_PASSWORD" | docker login "${NEXUS_REGISTRY}" -u "$NEXUS_USERNAME" --password-stdin; then
        log SUCCESS "Successfully logged in to Nexus registry."
    else
        log ERROR "Failed to login to Nexus registry. Please check credentials or registry status."
        exit 1
    fi
else
    log WARN "NEXUS_USERNAME or NEXUS_PASSWORD not set. Assuming Docker is already logged in to ${NEXUS_REGISTRY}."
    # Optionally, add a check here if login is strictly required
    # docker info | grep -q "Username:" || (log ERROR "Not logged in. Please login manually or provide NEXUS_USERNAME/PASSWORD." && exit 1)
fi

# =====================================================
# Build and Push Process
# =====================================================

# Set working directory to the script's directory to ensure relative paths work
cd "$(dirname "$0")"
log INFO "Working directory set to: $(pwd)"


# Use BuildKit for improved build performance
export DOCKER_BUILDKIT=1

log INFO "Starting build process..."

# --- Build Frontend ---
FRONTEND_IMAGE_NAME="${NEXUS_REGISTRY}/intric/frontend"
FRONTEND_IMAGE_FULL_TAG="${FRONTEND_IMAGE_NAME}:${IMAGE_TAG}"
FRONTEND_IMAGE_LATEST_TAG="${FRONTEND_IMAGE_NAME}:latest"
FRONTEND_CONTEXT_PATH="./frontend"
FRONTEND_DOCKERFILE_PATH="${FRONTEND_CONTEXT_PATH}/Dockerfile" # Assuming Dockerfile is in frontend dir

log INFO "Building frontend image: ${FRONTEND_IMAGE_FULL_TAG} from ${FRONTEND_DOCKERFILE_PATH}"
if docker build \
    --cache-from "${FRONTEND_IMAGE_LATEST_TAG}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    -t "${FRONTEND_IMAGE_FULL_TAG}" \
    -f "${FRONTEND_DOCKERFILE_PATH}" \
    "${FRONTEND_CONTEXT_PATH}"; then
    log SUCCESS "Frontend image built successfully: ${FRONTEND_IMAGE_FULL_TAG}"
else
    log ERROR "Failed to build frontend image"
    exit 1
fi

log INFO "Pushing frontend image to Nexus: ${FRONTEND_IMAGE_FULL_TAG}"

if docker push "${FRONTEND_IMAGE_FULL_TAG}"; then
    log SUCCESS "Frontend image pushed successfully: ${FRONTEND_IMAGE_FULL_TAG}"
else
    log ERROR "Failed to push frontend image"
    exit 1
fi

# --- Build Backend ---
BACKEND_IMAGE_NAME="${NEXUS_REGISTRY}/intric/backend"
BACKEND_IMAGE_FULL_TAG="${BACKEND_IMAGE_NAME}:${IMAGE_TAG}"
BACKEND_IMAGE_LATEST_TAG="${BACKEND_IMAGE_NAME}:latest"
BACKEND_CONTEXT_PATH="./backend"
BACKEND_DOCKERFILE_PATH="${BACKEND_CONTEXT_PATH}/Dockerfile" # Assuming Dockerfile is in backend dir

log INFO "Building backend image: ${BACKEND_IMAGE_FULL_TAG} from ${BACKEND_DOCKERFILE_PATH}"
# --- FIX: Removed --no-cache ---
if docker build \
    --cache-from "${BACKEND_IMAGE_LATEST_TAG}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    -t "${BACKEND_IMAGE_FULL_TAG}" \
    -f "${BACKEND_DOCKERFILE_PATH}" \
    "${BACKEND_CONTEXT_PATH}"; then
    log SUCCESS "Backend image built successfully: ${BACKEND_IMAGE_FULL_TAG}"
else
    log ERROR "Failed to build backend image"
    exit 1
fi

log INFO "Pushing backend image to Nexus: ${BACKEND_IMAGE_FULL_TAG}"
if docker push "${BACKEND_IMAGE_FULL_TAG}"; then
    log SUCCESS "Backend image pushed successfully: ${BACKEND_IMAGE_FULL_TAG}"
else
    log ERROR "Failed to push backend image"
    exit 1
fi



# =====================================================
# Tag and Push 'latest' (Conditional)
# =====================================================

# Tag as latest if:
# 1. The current tag is not already 'latest' AND
# 2. It's a semantic version OR the current branch is main/master
SHOULD_TAG_LATEST=false
if [ "$IMAGE_TAG" != "latest" ]; then
    if [[ $IMAGE_TAG =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$ ]] || \
       [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
        SHOULD_TAG_LATEST=true
    fi
fi

if [ "$SHOULD_TAG_LATEST" = true ]; then
    log INFO "Tagging images as latest..."
    if docker tag "${FRONTEND_IMAGE_FULL_TAG}" "${FRONTEND_IMAGE_LATEST_TAG}" && \
       docker tag "${BACKEND_IMAGE_FULL_TAG}" "${BACKEND_IMAGE_LATEST_TAG}"; then
        log SUCCESS "Images tagged as latest successfully."
    else
        log ERROR "Failed to tag images as latest."
        # Decide if this is a critical error or just a warning
        # exit 1
    fi

    log INFO "Pushing latest tags to Nexus..."
    if docker push "${FRONTEND_IMAGE_LATEST_TAG}" && \
       docker push "${BACKEND_IMAGE_LATEST_TAG}"; then
        log SUCCESS "Latest tags pushed successfully."
    else
        log ERROR "Failed to push latest tags."
        # Decide if this is a critical error or just a warning
        # exit 1
    fi
else
    log WARN "Skipping 'latest' tag push (not a SemVer tag and not on main/master branch, or already tagged as latest)."
fi


# =====================================================
# Summary
# =====================================================

log SUCCESS "Build and push complete!"
log SUCCESS "Frontend: ${FRONTEND_IMAGE_FULL_TAG}"
if [ "$SHOULD_TAG_LATEST" = true ]; then log SUCCESS "Frontend (latest): ${FRONTEND_IMAGE_LATEST_TAG}"; fi
log SUCCESS "Backend:  ${BACKEND_IMAGE_FULL_TAG}"
if [ "$SHOULD_TAG_LATEST" = true ]; then log SUCCESS "Backend (latest):  ${BACKEND_IMAGE_LATEST_TAG}"; fi
echo ""
log INFO "To deploy in production:"
echo "1. Ensure NEXUS_REGISTRY and IMAGE_TAG (e.g., ${IMAGE_TAG}) environment variables are set on the production server."
echo "2. Run: docker compose pull"
echo "3. Run: docker compose up -d"
echo "4. For the very first deployment or after database schema changes:"
echo "   docker compose --profile init up db-init"
