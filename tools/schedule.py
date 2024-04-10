from functools import partial

def get_int_from_list_or_default(l, idx, default_val):
    return int(l[idx]) if idx < len(l) else default_val


def get_recommended_maximum_batch_size(args):
    ml_server = args.remote_ml_server_type
    if ml_server == "sagemaker":
        return 100  # sagemaker doesn't have a restriction, it's magic number for now
    elif ml_server == "cohere":
        # https://docs.cohere.com/reference/embed
        return 96
    elif ml_server == "openai":
        # https://community.openai.com/t/embeddings-api-max-batch-size/655329
        return 2048
    else:  # ml_server == "unknown"
        return 200


def exceeding_bound_check(bound, trend, current):
    if trend > 0:
        return current > bound
    else:
        return current < bound


def exceeding_and_equal_check(bound, trend, current):
    if trend > 0:
        return current >= bound
    else:
        return current <= bound


class Schedule(object):
    def __init__(self, single_val, schedule_val, default_minimal, default_maximal, default_step_size):
        self.default_step_size = default_step_size
        self.default_maximal = default_maximal
        self.default_minimal = default_minimal
        self.schedule_val = schedule_val
        self.single_val = single_val
        self.steps = self._get_steps()

    def _get_steps(self):
        if self.schedule_val:
            # user specified schedule "@10:20:90"
            if self.schedule_val[0] == "@":
                schedule = self.schedule_val[1:]
                return [int(s) for s in schedule.split(":")]
            # a pattern to calculate schedule
            else:
                sections = [] if self.schedule_val is None else self.schedule_val.split(":")
                minimum_batch_size = get_int_from_list_or_default(sections, 0, self.default_minimal)
                maximum_batch_size = get_int_from_list_or_default(sections, 1, self.default_maximal)
                trend = 1 if get_int_from_list_or_default(sections, 2, 1) > 0 else -1
                step_size = get_int_from_list_or_default(sections, 3, self.default_step_size)
                current = minimum_batch_size if trend > 0 else maximum_batch_size

                steps = []
                open_bound_check = partial(exceeding_bound_check,
                                           maximum_batch_size if trend > 0 else minimum_batch_size, trend)
                close_bound_check = partial(exceeding_and_equal_check,
                                            maximum_batch_size if trend > 0 else minimum_batch_size, trend)
                while not open_bound_check(current):
                    steps.append(current)
                    previous = current
                    current = current + trend * step_size
                    if not close_bound_check(previous):
                        current = min(current, maximum_batch_size) if trend > 0 else max(current, minimum_batch_size)
                return steps
        else:
            return [int(self.single_val)]


class BatchSizeSchedule(Schedule):
    def __init__(self, args):
        super().__init__(args.batch_size, args.batch_size_schedule, 1, get_recommended_maximum_batch_size(args),
                         20)


class BulkSizeSchedule(Schedule):
    def __init__(self, args):
        super().__init__(args.bulk_size, args.bulk_size_schedule, 100, 1000, 100)


class ClientSchedule(Schedule):
    def __init__(self, args):
        super().__init__(args.client, args.client_schedule, 1, 10, 1)
