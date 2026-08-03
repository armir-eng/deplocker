import * as yup from "yup";

export const DashboardMenu = yup
  .string()
  .oneOf(["projects", "deployments"])
  .required();

export const ProjectCreateRequest = yup.object().shape({
  name: yup.string().required(),
  description: yup.string().required(),
});

export const ProjectCreateResponse = yup
  .object()
  .shape({
    id: yup.string().uuid().required(),
    slug: yup.string().required(),
    created_at: yup.string().datetime().required(),
    updated_at: yup.string().datetime().required(),
    status: yup.string().oneOf(["created"]).required(),
  })
  .concat(ProjectCreateRequest);
