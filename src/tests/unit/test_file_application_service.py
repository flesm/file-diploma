import pytest

from src.app.application.services import FileApplicationService


class TestFileApplicationService:
    async def test_create_upload_link_persists_pending_asset(
        self,
        file_repository,
        material_repository,
        storage_gateway,
        access_gateway,
        mentor_viewer,
    ) -> None:
        service = FileApplicationService(
            file_repository,
            material_repository,
            storage_gateway,
            access_gateway,
        )

        result = await service.create_upload_link(
            viewer=mentor_viewer,
            file_name="spec.pdf",
            content_type="application/pdf",
            size=128,
            category="materials",
        )

        assert result["bucket"] == "materials"
        file_repository.create.assert_awaited_once()

    async def test_complete_upload_updates_status(
        self,
        file_repository,
        material_repository,
        storage_gateway,
        access_gateway,
        mentor_viewer,
        file_asset,
    ) -> None:
        file_repository.get_by_id.return_value = file_asset
        service = FileApplicationService(
            file_repository,
            material_repository,
            storage_gateway,
            access_gateway,
        )

        result = await service.complete_upload(mentor_viewer, file_asset.id)

        assert result.status == "uploaded"
        storage_gateway.ensure_object_exists.assert_called_once_with(
            file_asset.object_key
        )
        file_repository.update.assert_awaited_once()

    async def test_get_download_link_raises_for_missing_file(
        self,
        file_repository,
        material_repository,
        storage_gateway,
        access_gateway,
    ) -> None:
        file_repository.get_by_id.return_value = None
        service = FileApplicationService(
            file_repository,
            material_repository,
            storage_gateway,
            access_gateway,
        )

        with pytest.raises(ValueError):
            await service.get_download_link("missing")

    async def test_create_material_for_selected_interns_checks_access(
        self,
        file_repository,
        material_repository,
        storage_gateway,
        access_gateway,
        mentor_viewer,
        file_asset,
    ) -> None:
        file_repository.get_by_id.return_value = file_asset
        access_gateway.get_mentor_intern_ids.return_value = ["intern-1", "intern-2"]
        service = FileApplicationService(
            file_repository,
            material_repository,
            storage_gateway,
            access_gateway,
        )

        result = await service.create_material(
            viewer=mentor_viewer,
            title="Architecture",
            description="Overview",
            file_id=file_asset.id,
            audience_scope="selected_interns",
            target_intern_ids=["intern-1"],
        )

        assert result.target_intern_ids == ["intern-1"]
        material_repository.create.assert_awaited_once()

    async def test_create_material_rejects_non_mentor(
        self,
        file_repository,
        material_repository,
        storage_gateway,
        access_gateway,
        intern_viewer,
    ) -> None:
        service = FileApplicationService(
            file_repository,
            material_repository,
            storage_gateway,
            access_gateway,
        )

        with pytest.raises(ValueError):
            await service.create_material(
                viewer=intern_viewer,
                title="Architecture",
                description="Overview",
                file_id="file-1",
                audience_scope="all_interns",
                target_intern_ids=[],
            )

    async def test_list_materials_for_intern_applies_visibility_rules(
        self,
        file_repository,
        material_repository,
        storage_gateway,
        access_gateway,
        intern_viewer,
        material,
    ) -> None:
        own_group = material.__class__(**{**material.__dict__, "audience_scope": "own_interns"})
        all_interns = material.__class__(
            **{
                **material.__dict__,
                "id": "material-2",
                "audience_scope": "all_interns",
            }
        )
        hidden = material.__class__(
            **{
                **material.__dict__,
                "id": "material-3",
                "target_intern_ids": ["intern-2"],
            }
        )
        own_group.id = "material-4"
        material_repository.list_all.return_value = [
            material,
            own_group,
            all_interns,
            hidden,
        ]
        access_gateway.get_my_mentor_id.return_value = "mentor-1"
        service = FileApplicationService(
            file_repository,
            material_repository,
            storage_gateway,
            access_gateway,
        )

        result = await service.list_materials_for_viewer(intern_viewer)

        assert [item.id for item in result] == [
            "material-1",
            "material-4",
            "material-2",
        ]
