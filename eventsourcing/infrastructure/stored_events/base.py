from abc import ABCMeta, abstractmethod

import six

from eventsourcing.infrastructure.stored_events.transcoders import serialize_domain_event, deserialize_domain_event


class StoredEventRepository(six.with_metaclass(ABCMeta)):

    serialize_without_json = False
    serialize_with_uuid1 = False

    def __init__(self, json_encoder_cls=None, json_decoder_cls=None):
        self.json_encoder_cls = json_encoder_cls
        self.json_decoder_cls = json_decoder_cls

    @abstractmethod
    def append(self, stored_event):
        """Saves given stored event in this repository.
        :param stored_event: 
        """

    @abstractmethod
    def __getitem__(self, event_id):
        """Returns stored event for given event ID.
        """

    @abstractmethod
    def __contains__(self, event_id):
        """Tests whether given event ID exists.
        """

    @abstractmethod
    def get_entity_events(self, stored_entity_id, since=None, before=None, limit=None):
        """Returns all events for given entity ID in chronological order.
        :param before:
        :param since:
        :param stored_entity_id:
        :rtype: list
        """

    @abstractmethod
    def get_most_recent_event(self, stored_entity_id):
        """Returns last event for given entity ID.

        :param stored_entity_id:
        :rtype: DomainEvent, NoneType
        """

    @abstractmethod
    def get_topic_events(self, event_topic):
        """Returns all events for given topic.
        :param event_topic: 
        """

    def serialize(self, domain_event):
        """Returns a stored event from a domain event.
        :type domain_event: object
        :param domain_event:
        """
        return serialize_domain_event(
            domain_event,
            json_encoder_cls=self.json_encoder_cls,
            without_json=self.serialize_without_json,
            with_uuid1=self.serialize_with_uuid1
        )

    def deserialize(self, stored_event):
        """Returns a domain event from a stored event.
        :type stored_event: object
        """
        return deserialize_domain_event(
            stored_event,
            json_decoder_cls=self.json_decoder_cls,
            without_json=self.serialize_without_json
        )

    @staticmethod
    def map(func, iterable):
        return six.moves.map(func, iterable)


class StoredEventIterator(object):

    def __init__(self, repo, stored_entity_id, page_size=1000, since=None, before=None, limit=None):
        assert isinstance(repo, StoredEventRepository)
        assert isinstance(stored_entity_id, six.string_types)
        assert isinstance(page_size, six.integer_types)
        self.repo = repo
        self.stored_entity_id = stored_entity_id
        self.page_size = page_size
        self.since = since
        self.before = before
        self.limit = limit

    def __iter__(self):
        if self.limit is None:
            limit = self.limit
        else:
            limit = min(self.page_size, self.limit)
        while True:
            retrieved_events = self.repo.get_entity_events(self.stored_entity_id,
                                                           since=self.since,
                                                           before=self.before,
                                                           limit=limit
                                                           )
            count = 0
            for stored_event in retrieved_events:
                yield stored_event
                self.since = stored_event.event_id
                count += 1
            if not count == self.page_size:
                raise StopIteration