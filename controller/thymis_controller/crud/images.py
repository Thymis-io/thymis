import logging
import time

from thymis_controller.config import global_settings

logger = logging.getLogger(__name__)


def cleanup_old_images() -> int:
    """
    Clean up images that haven't been accessed in 30 minutes.
    Returns the number of images deleted.
    """
    image_dir = global_settings.PROJECT_PATH / "images"
    if not image_dir.exists():
        return 0

    current_time = time.time()
    cutoff_time = current_time - (30 * 60)  # 30 minutes ago

    deleted_count = 0
    image_patterns = ["*.img", "*.qcow2", "*.iso", "*.start-vm"]

    for pattern in image_patterns:
        for image_path in image_dir.glob(pattern):
            try:
                # Get the last access time (atime) of the file
                stat_info = image_path.stat()
                last_access_time = stat_info.st_atime

                # Only delete if the image hasn't been accessed in 30 minutes
                if last_access_time < cutoff_time:
                    logger.info(
                        "Deleting old image: %s (last accessed: %d minutes ago)",
                        image_path.name,
                        int((current_time - last_access_time) / 60),
                    )
                    if image_path.is_file():
                        image_path.unlink()
                        deleted_count += 1
                    elif image_path.is_dir():
                        # Handle directories (like nixos-vm directories)
                        import shutil

                        shutil.rmtree(image_path)
                        deleted_count += 1
            except OSError as e:
                logger.warning("Failed to delete image %s: %s", image_path, e)
                continue

    if deleted_count > 0:
        logger.info("Deleted %d old images", deleted_count)

    return deleted_count


async def periodic_image_cleanup() -> int:
    """
    Periodically clean up old images.
    This function is designed to be called from the main cleanup loop.
    """
    return cleanup_old_images()
