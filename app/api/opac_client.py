"""
OPAC (Online Public Access Catalog) Client for library system integration
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)


class OPACClient:
    """Client for interacting with various OPAC systems"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize OPAC client with configuration

        Args:
            config: Dictionary containing OPAC configuration
                  - opac_type: 'koha', 'evergreen', 'sierra', 'aleph', 'generic'
                  - base_url: Base URL of OPAC API
                  - api_key: API key for authentication
                  - username: Username for basic auth
                  - password: Password for basic auth
                  - timeout: Request timeout in seconds
        """
        self.config = config or {}

        # Set default values
        self.opac_type = self.config.get('opac_type', 'generic').lower()
        self.base_url = self.config.get('base_url', '').rstrip('/')
        self.api_key = self.config.get('api_key')
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        self.timeout = self.config.get('timeout', 30)

        # OPAC-specific endpoints
        self.endpoints = self._get_endpoints()

        # Session for connection pooling
        self.session = requests.Session()

        # Set up authentication
        self._setup_auth()

        # Test connection on initialization
        if self.base_url:
            self._test_connection()

    def _get_endpoints(self) -> Dict[str, str]:
        """Get OPAC-specific API endpoints"""

        endpoints = {
            'koha': {
                'search': '/cgi-bin/koha/opac-search.pl',
                'biblios': '/api/v1/biblios',
                'availability': '/api/v1/availability',
                'holdings': '/api/v1/holdings'
            },
            'evergreen': {
                'search': '/osrf-webservices-translator/open-ils.search',
                'record': '/osrf-webservices-translator/open-ils.cat'
            },
            'generic': {
                'search': '/search',
                'record': '/records'
            }
        }

        # Use configured type or default to generic
        opac_type = self.opac_type if self.opac_type in endpoints else 'generic'
        return endpoints.get(opac_type, endpoints['generic'])

    def _setup_auth(self):
        """Set up authentication for the session"""
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'X-API-Key': self.api_key
            })
        elif self.username and self.password:
            self.session.auth = (self.username, self.password)

    def _test_connection(self):
        """Test connection to OPAC system"""
        try:
            if self.base_url:
                response = self.session.get(f"{self.base_url}/", timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ Connected to OPAC system at {self.base_url}")
                else:
                    logger.warning(f"⚠️ OPAC system responded with status {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to OPAC system: {e}")

    def search(self, query: str = '', author: str = '', title: str = '',
               subject: str = '', isbn: str = '', limit: int = 20) -> List[Dict]:
        """
        Search the library catalog

        Args:
            query: General search query
            author: Author name
            title: Book title
            subject: Subject/topic
            isbn: ISBN number
            limit: Maximum results to return

        Returns:
            List of book records
        """

        # Build search parameters
        search_params = self._build_search_params(query, author, title, subject, isbn)

        try:
            # Choose appropriate search method based on OPAC type
            if self.opac_type == 'koha':
                results = self._search_koha(search_params, limit)
            elif self.opac_type == 'evergreen':
                results = self._search_evergreen(search_params, limit)
            else:
                results = self._search_generic(search_params, limit)

            # Enrich results with local data if needed
            enriched_results = self._enrich_results(results)

            return enriched_results[:limit]

        except Exception as e:
            logger.error(f"Error searching OPAC: {e}")
            # Fallback to local search or empty results
            return self._fallback_search(search_params, limit)

    def _build_search_params(self, query: str, author: str, title: str,
                             subject: str, isbn: str) -> Dict[str, str]:
        """Build search parameters dictionary"""
        params = {}

        if query:
            params['q'] = query
        if author:
            params['author'] = author
        if title:
            params['title'] = title
        if subject:
            params['subject'] = subject
        if isbn:
            params['isbn'] = isbn

        return params

    def _search_koha(self, params: Dict, limit: int) -> List[Dict]:
        """Search Koha OPAC system"""
        try:
            # Koha search endpoint
            search_url = f"{self.base_url}{self.endpoints.get('search', '/cgi-bin/koha/opac-search.pl')}"

            # Koha expects specific parameters
            koha_params = {}
            if 'q' in params:
                koha_params['q'] = params['q']
            if 'author' in params:
                koha_params['q'] = f"au:{params['author']}" if not koha_params.get(
                    'q') else f"{koha_params['q']} au:{params['author']}"
            if 'title' in params:
                koha_params['q'] = f"ti:{params['title']}" if not koha_params.get(
                    'q') else f"{koha_params['q']} ti:{params['title']}"

            koha_params['format'] = 'json'
            koha_params['limit'] = limit

            response = self.session.get(search_url, params=koha_params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                return self._parse_koha_results(data)
            else:
                logger.error(f"Koha search failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Koha search error: {e}")
            return []

    def _search_evergreen(self, params: Dict, limit: int) -> List[Dict]:
        """Search Evergreen OPAC system"""
        try:
            # Evergreen uses XML-RPC style API
            search_url = f"{self.base_url}{self.endpoints.get('search', '/osrf-webservices-translator/open-ils.search')}"

            # Build Evergreen search request
            search_request = {
                "method": "open-ils.search.biblio.multiclass.query",
                "params": [self._build_evergreen_params(params)],
                "id": 1
            }

            response = self.session.post(search_url, json=search_request, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                return self._parse_evergreen_results(data)
            else:
                logger.error(f"Evergreen search failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Evergreen search error: {e}")
            return []

    def _search_generic(self, params: Dict, limit: int) -> List[Dict]:
        """Generic search for any OPAC with SRU/OpenSearch"""
        try:
            # Try SRU (Search/Retrieve via URL) protocol first
            if self._supports_sru():
                return self._search_sru(params, limit)

            # Try OpenSearch
            if self._supports_opensearch():
                return self._search_opensearch(params, limit)

            # Fallback to simple HTTP search
            search_url = f"{self.base_url}{self.endpoints.get('search', '/search')}"

            # Add limit to params
            params['limit'] = limit
            params['format'] = 'json'

            response = self.session.get(search_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                return self._parse_generic_results(data)
            else:
                logger.error(f"Generic search failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Generic search error: {e}")
            return []

    def _search_sru(self, params: Dict, limit: int) -> List[Dict]:
        """Search using SRU protocol"""
        try:
            sru_url = f"{self.base_url}/sru"

            # Build CQL query for SRU
            cql_query = self._build_cql_query(params)

            sru_params = {
                'operation': 'searchRetrieve',
                'version': '1.1',
                'recordSchema': 'marcxml',
                'maximumRecords': limit,
                'query': cql_query
            }

            response = self.session.get(sru_url, params=sru_params, timeout=self.timeout)

            if response.status_code == 200:
                # Parse SRU XML response
                return self._parse_sru_results(response.content)
            else:
                return []

        except Exception as e:
            logger.error(f"SRU search error: {e}")
            return []

    def _search_opensearch(self, params: Dict, limit: int) -> List[Dict]:
        """Search using OpenSearch protocol"""
        try:
            opensearch_url = f"{self.base_url}/opensearch"

            # Build OpenSearch query
            search_terms = []
            if 'q' in params:
                search_terms.append(params['q'])
            if 'author' in params:
                search_terms.append(f"author:{params['author']}")
            if 'title' in params:
                search_terms.append(f"title:{params['title']}")

            query = ' '.join(search_terms)

            opensearch_params = {
                'searchTerms': query,
                'count': limit,
                'format': 'json'
            }

            response = self.session.get(opensearch_url, params=opensearch_params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                return self._parse_opensearch_results(data)
            else:
                return []

        except Exception as e:
            logger.error(f"OpenSearch error: {e}")
            return []

    def _build_cql_query(self, params: Dict) -> str:
        """Build CQL query for SRU protocol"""
        conditions = []

        if 'author' in params:
            conditions.append(f'dc.creator all "{params["author"]}"')
        if 'title' in params:
            conditions.append(f'dc.title all "{params["title"]}"')
        if 'subject' in params:
            conditions.append(f'dc.subject all "{params["subject"]}"')
        if 'isbn' in params:
            conditions.append(f'dc.identifier all "{params["isbn"]}"')
        if 'q' in params:
            conditions.append(f'any all "{params["q"]}"')

        return ' and '.join(conditions) if conditions else 'cql.serverChoice all ""'

    def _build_evergreen_params(self, params: Dict) -> Dict:
        """Build parameters for Evergreen search"""
        evergreen_params = {
            "search_ou": 1,  # Default org unit
            "depth": 0,
            "limit": 10,
            "offset": 0
        }

        # Add search terms
        search_terms = []
        for key, value in params.items():
            if value:
                search_terms.append({
                    "field": key,
                    "value": value,
                    "op": "=="
                })

        if search_terms:
            evergreen_params["filters"] = search_terms

        return evergreen_params

    def _parse_koha_results(self, data: Dict) -> List[Dict]:
        """Parse Koha API results"""
        results = []

        if 'biblios' in data:
            for biblio in data['biblios']:
                result = {
                    'id': biblio.get('biblionumber'),
                    'title': biblio.get('title'),
                    'author': biblio.get('author'),
                    'isbn': biblio.get('isbn'),
                    'publication_year': biblio.get('copyrightdate'),
                    'subject': biblio.get('subject'),
                    'call_number': biblio.get('itemcallnumber'),
                    'availability': self._parse_koha_availability(biblio),
                    'source': 'koha'
                }
                results.append(result)

        return results

    def _parse_koha_availability(self, biblio: Dict) -> Dict:
        """Parse availability information from Koha"""
        items = biblio.get('items', [])

        available_count = 0
        total_count = len(items)

        for item in items:
            if item.get('notforloan') == 0 and item.get('withdrawn') == 0:
                available_count += 1

        return {
            'available': available_count > 0,
            'available_count': available_count,
            'total_count': total_count,
            'status': 'Available' if available_count > 0 else 'Checked Out'
        }

    def _parse_evergreen_results(self, data: Dict) -> List[Dict]:
        """Parse Evergreen API results"""
        results = []

        # Evergreen response format varies
        if 'result' in data:
            records = data['result']

            for record in records:
                result = {
                    'id': record.get('id'),
                    'title': record.get('title'),
                    'author': record.get('author'),
                    'isbn': record.get('isbn'),
                    'publication_year': record.get('pubdate'),
                    'subject': record.get('subject'),
                    'call_number': record.get('call_number'),
                    'availability': {'available': True, 'source': 'evergreen'},
                    'source': 'evergreen'
                }
                results.append(result)

        return results

    def _parse_generic_results(self, data: Any) -> List[Dict]:
        """Parse generic JSON results"""
        results = []

        # Try different common response formats
        if isinstance(data, list):
            # Direct list of records
            records = data
        elif isinstance(data, dict):
            # Dictionary with records key
            records = data.get('records', data.get('results', data.get('items', [])))
        else:
            records = []

        for record in records:
            if isinstance(record, dict):
                result = {
                    'id': record.get('id', record.get('bibid', record.get('record_id'))),
                    'title': record.get('title', record.get('name', '')),
                    'author': record.get('author', record.get('creator', '')),
                    'isbn': record.get('isbn', record.get('identifier')),
                    'publication_year': record.get('year', record.get('publication_year', record.get('date'))),
                    'subject': record.get('subject', record.get('topic', '')),
                    'call_number': record.get('call_number', record.get('callNumber', '')),
                    'availability': record.get('availability', {'available': True}),
                    'source': 'generic'
                }
                results.append(result)

        return results

    def _parse_sru_results(self, xml_content: bytes) -> List[Dict]:
        """Parse SRU XML results"""
        results = []

        try:
            root = ET.fromstring(xml_content)

            # Namespace handling
            ns = {
                'srw': 'http://www.loc.gov/zing/srw/',
                'marc': 'http://www.loc.gov/MARC21/slim'
            }

            for record in root.findall('.//srw:record', ns):
                record_data = record.find('.//marc:record', ns)

                if record_data is not None:
                    result = self._parse_marc_record(record_data)
                    result['source'] = 'sru'
                    results.append(result)

        except Exception as e:
            logger.error(f"Error parsing SRU XML: {e}")

        return results

    def _parse_marc_record(self, record: ET.Element) -> Dict:
        """Parse MARC XML record"""
        result = {
            'id': '',
            'title': '',
            'author': '',
            'isbn': '',
            'publication_year': '',
            'subject': '',
            'call_number': ''
        }

        # Namespace for MARC
        ns = {'marc': 'http://www.loc.gov/MARC21/slim'}

        # Extract control field (001 for record ID)
        control_field = record.find('.//marc:controlfield[@tag="001"]', ns)
        if control_field is not None:
            result['id'] = control_field.text or ''

        # Extract data fields
        for datafield in record.findall('.//marc:datafield', ns):
            tag = datafield.get('tag', '')

            if tag == '245':  # Title
                subfield_a = datafield.find('.//marc:subfield[@code="a"]', ns)
                if subfield_a is not None:
                    result['title'] = subfield_a.text or ''

            elif tag == '100':  # Author (personal name)
                subfield_a = datafield.find('.//marc:subfield[@code="a"]', ns)
                if subfield_a is not None:
                    result['author'] = subfield_a.text or ''

            elif tag == '020':  # ISBN
                subfield_a = datafield.find('.//marc:subfield[@code="a"]', ns)
                if subfield_a is not None:
                    result['isbn'] = subfield_a.text or ''

            elif tag == '260':  # Publication info
                subfield_c = datafield.find('.//marc:subfield[@code="c"]', ns)
                if subfield_c is not None:
                    result['publication_year'] = subfield_c.text or ''

            elif tag == '650':  # Subject
                subfield_a = datafield.find('.//marc:subfield[@code="a"]', ns)
                if subfield_a is not None:
                    result['subject'] = subfield_a.text or ''

            elif tag == '090':  # Local call number
                subfield_a = datafield.find('.//marc:subfield[@code="a"]', ns)
                if subfield_a is not None:
                    result['call_number'] = subfield_a.text or ''

        return result

    def _parse_opensearch_results(self, data: Dict) -> List[Dict]:
        """Parse OpenSearch results"""
        results = []

        # OpenSearch RSS or JSON format
        if 'rss' in data or 'channel' in data:
            # RSS format
            pass  # Implement RSS parsing if needed
        elif 'entries' in data:
            # JSON feed format
            for entry in data['entries']:
                result = {
                    'id': entry.get('id', ''),
                    'title': entry.get('title', ''),
                    'author': entry.get('author', {}).get('name', '') if isinstance(entry.get('author'),
                                                                                    dict) else entry.get('author', ''),
                    'isbn': entry.get('isbn', ''),
                    'publication_year': entry.get('published', ''),
                    'subject': entry.get('subject', ''),
                    'call_number': entry.get('call_number', ''),
                    'availability': {'available': True},
                    'source': 'opensearch'
                }
                results.append(result)

        return results

    def _enrich_results(self, results: List[Dict]) -> List[Dict]:
        """Enrich results with additional information"""
        for result in results:
            # Add timestamp
            result['retrieved_at'] = datetime.now().isoformat()

            # Format author name
            if result.get('author'):
                result['author_formatted'] = self._format_author(result['author'])

            # Clean ISBN
            if result.get('isbn'):
                result['isbn_clean'] = self._clean_isbn(result['isbn'])

            # Add search relevance score (simplified)
            result['relevance_score'] = 0.8  # Placeholder

        return results

    def _format_author(self, author: str) -> str:
        """Format author name for display"""
        if ',' in author:
            parts = author.split(',', 1)
            if len(parts) == 2:
                return f"{parts[1].strip()} {parts[0].strip()}"
        return author

    def _clean_isbn(self, isbn: str) -> str:
        """Clean ISBN by removing non-numeric characters except X"""
        cleaned = ''.join(c for c in isbn if c.isdigit() or c.upper() == 'X')
        return cleaned

    def _fallback_search(self, params: Dict, limit: int) -> List[Dict]:
        """Fallback search when OPAC is unavailable"""
        logger.info("Using fallback search (no OPAC connection)")

        # Return empty results or cached/sample data
        return [
            {
                'id': 'fallback-1',
                'title': 'Sample Book: Introduction to Computer Science',
                'author': 'John Smith',
                'isbn': '9780123456789',
                'publication_year': '2023',
                'subject': 'Computer Science',
                'call_number': 'QA76.123',
                'availability': {'available': True, 'available_count': 1},
                'source': 'fallback',
                'note': 'OPAC system unavailable. Showing sample data.'
            }
        ]

    def _supports_sru(self) -> bool:
        """Check if OPAC supports SRU protocol"""
        if not self.base_url:
            return False

        try:
            # Try to discover SRU service
            sru_url = f"{self.base_url}/sru"
            response = self.session.head(sru_url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def _supports_opensearch(self) -> bool:
        """Check if OPAC supports OpenSearch"""
        if not self.base_url:
            return False

        try:
            # Try to discover OpenSearch description
            osd_url = f"{self.base_url}/opensearchdescription.xml"
            response = self.session.head(osd_url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_book_details(self, book_id: str) -> Optional[Dict]:
        """Get detailed information about a specific book"""
        try:
            if self.opac_type == 'koha':
                url = f"{self.base_url}{self.endpoints.get('biblios', '/api/v1/biblios')}/{book_id}"
            else:
                url = f"{self.base_url}{self.endpoints.get('record', '/records')}/{book_id}"

            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                return self._parse_book_details(data)
            else:
                logger.error(f"Failed to get book details: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting book details: {e}")
            return None

    def _parse_book_details(self, data: Dict) -> Dict:
        """Parse detailed book information"""
        details = {
            'id': data.get('id', ''),
            'title': data.get('title', ''),
            'author': data.get('author', ''),
            'isbn': data.get('isbn', ''),
            'publication_year': data.get('publication_year', data.get('year', '')),
            'publisher': data.get('publisher', ''),
            'place_of_publication': data.get('place_of_publication', ''),
            'physical_description': data.get('physical_description', ''),
            'edition': data.get('edition', ''),
            'series': data.get('series', ''),
            'notes': data.get('notes', ''),
            'summary': data.get('summary', data.get('abstract', '')),
            'subjects': data.get('subjects', []),
            'language': data.get('language', ''),
            'pages': data.get('pages', ''),
            'cover_image': data.get('cover_image', data.get('thumbnail', '')),
            'holdings': data.get('holdings', []),
            'availability': data.get('availability', {'available': False}),
            'source': self.opac_type
        }

        return details

    def check_availability(self, book_id: str) -> Dict:
        """Check availability of a specific book"""
        try:
            if self.opac_type == 'koha':
                url = f"{self.base_url}{self.endpoints.get('availability', '/api/v1/availability')}/{book_id}"
            else:
                # Generic availability check
                details = self.get_book_details(book_id)
                if details:
                    return details.get('availability', {'available': False})
                return {'available': False}

            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                return self._parse_availability(data)
            else:
                logger.error(f"Failed to check availability: {response.status_code}")
                return {'available': False, 'error': 'Failed to check availability'}

        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {'available': False, 'error': str(e)}

    def _parse_availability(self, data: Dict) -> Dict:
        """Parse availability information"""
        availability = {
            'available': data.get('available', False),
            'available_count': data.get('available_count', 0),
            'total_count': data.get('total_count', 0),
            'holds_count': data.get('holds_count', 0),
            'due_date': data.get('due_date'),
            'status': 'Available' if data.get('available', False) else 'Checked Out',
            'locations': data.get('locations', []),
            'call_numbers': data.get('call_numbers', [])
        }

        return availability


# Mock OPAC Client for development
class MockOPACClient(OPACClient):
    """Mock OPAC client for development and testing"""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        logger.info("Using MockOPACClient for development")

        # Sample data for testing
        self.sample_books = [
            {
                'id': '1',
                'title': 'Introduction to Algorithms',
                'author': 'Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein',
                'isbn': '9780262033848',
                'publication_year': '2009',
                'subject': 'Computer Science, Algorithms',
                'call_number': 'QA76.6 .C662 2009',
                'availability': {'available': True, 'available_count': 3, 'total_count': 5},
                'publisher': 'MIT Press',
                'summary': 'Comprehensive introduction to modern algorithms.',
                'pages': '1292'
            },
            {
                'id': '2',
                'title': 'Clean Code: A Handbook of Agile Software Craftsmanship',
                'author': 'Robert C. Martin',
                'isbn': '9780132350884',
                'publication_year': '2008',
                'subject': 'Software Engineering, Programming',
                'call_number': 'QA76.76.D47 M365 2008',
                'availability': {'available': False, 'available_count': 0, 'total_count': 2},
                'publisher': 'Prentice Hall',
                'summary': 'Guidelines for writing clean, maintainable code.',
                'pages': '464'
            },
            {
                'id': '3',
                'title': 'The Pragmatic Programmer',
                'author': 'Andrew Hunt, David Thomas',
                'isbn': '9780201616224',
                'publication_year': '1999',
                'subject': 'Software Development',
                'call_number': 'QA76.D47 H86 1999',
                'availability': {'available': True, 'available_count': 1, 'total_count': 3},
                'publisher': 'Addison-Wesley',
                'summary': 'Your journey to mastery in software development.',
                'pages': '352'
            },
            {
                'id': '4',
                'title': 'Artificial Intelligence: A Modern Approach',
                'author': 'Stuart Russell, Peter Norvig',
                'isbn': '9780136042594',
                'publication_year': '2010',
                'subject': 'Artificial Intelligence',
                'call_number': 'Q335 .R86 2010',
                'availability': {'available': True, 'available_count': 2, 'total_count': 4},
                'publisher': 'Prentice Hall',
                'summary': 'The leading textbook in artificial intelligence.',
                'pages': '1152'
            },
            {
                'id': '5',
                'title': 'Deep Learning',
                'author': 'Ian Goodfellow, Yoshua Bengio, Aaron Courville',
                'isbn': '9780262035613',
                'publication_year': '2016',
                'subject': 'Machine Learning, Deep Learning',
                'call_number': 'Q325.5 .G66 2016',
                'availability': {'available': True, 'available_count': 1, 'total_count': 2},
                'publisher': 'MIT Press',
                'summary': 'Comprehensive textbook on deep learning.',
                'pages': '800'
            }
        ]

    def search(self, query: str = '', author: str = '', title: str = '',
               subject: str = '', isbn: str = '', limit: int = 20) -> List[Dict]:
        """Mock search implementation"""

        results = []

        for book in self.sample_books:
            match = False

            # Simple text matching for demonstration
            search_text = f"{book['title']} {book['author']} {book['subject']} {book['isbn']}".lower()

            if query and query.lower() in search_text:
                match = True
            elif author and author.lower() in book['author'].lower():
                match = True
            elif title and title.lower() in book['title'].lower():
                match = True
            elif subject and subject.lower() in book['subject'].lower():
                match = True
            elif isbn and isbn in book['isbn']:
                match = True
            elif not query and not author and not title and not subject and not isbn:
                # Return all books if no search criteria
                match = True

            if match:
                # Add relevance score based on matching
                relevance = 0.8
                if query and query.lower() in book['title'].lower():
                    relevance = 0.95

                book_copy = book.copy()
                book_copy['relevance_score'] = relevance
                book_copy['source'] = 'mock'
                book_copy['retrieved_at'] = datetime.now().isoformat()

                results.append(book_copy)

        # Sort by relevance score
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        return results[:limit]

    def get_book_details(self, book_id: str) -> Optional[Dict]:
        """Mock get book details"""
        for book in self.sample_books:
            if book['id'] == book_id:
                book_copy = book.copy()
                book_copy['source'] = 'mock'
                return book_copy

        return None

    def check_availability(self, book_id: str) -> Dict:
        """Mock availability check"""
        for book in self.sample_books:
            if book['id'] == book_id:
                return book.get('availability', {'available': False})

        return {'available': False, 'error': 'Book not found'}


# Factory function to create appropriate OPAC client
def create_opac_client(config: Optional[Dict] = None) -> OPACClient:
    """
    Factory function to create appropriate OPAC client

    Args:
        config: Configuration dictionary

    Returns:
        OPACClient instance (real or mock)
    """
    config = config or {}

    # Get config values
    opac_type = config.get('opac_type', 'openlibrary').lower()
    base_url = config.get('base_url', '')
    use_mock = config.get('use_mock', False)

    # Priority: OpenLibrary > use_mock setting > other OPAC types
    if opac_type == 'openlibrary':
        logger.info("Using OpenLibrary API client")
        return OpenLibraryClient(config)
    elif use_mock:
        logger.info("Using MockOPACClient for development")
        return MockOPACClient(config)
    elif base_url:
        logger.info(f"Using real OPAC client for {opac_type}")
        return OPACClient(config)
    else:
        # Default to OpenLibrary if no config
        logger.info("Using OpenLibrary API client (default)")
        return OpenLibraryClient(config)


class OpenLibraryClient:
    """
    Client for interacting with OpenLibrary API (openlibrary.org)
    """

    BASE_URL = "https://openlibrary.org"
    COVERS_URL = "https://covers.openlibrary.org"

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize OpenLibrary client

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.timeout = self.config.get('timeout', 30)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LibraryAIChatbot/1.0 (https://github.com/library-ai-chatbot)'
        })

    def search(self, query: str = '', author: str = '', title: str = '',
               subject: str = '', isbn: str = '', limit: int = 20) -> List[Dict]:
        """
        Search for books using OpenLibrary API

        Args:
            query: General search query
            author: Author name filter
            title: Title filter
            subject: Subject filter
            isbn: ISBN filter
            limit: Maximum number of results

        Returns:
            List of book results
        """
        try:
            # Build search parameters
            params = {}
            
            if isbn:
                # ISBN search is more precise
                search_url = f"{self.BASE_URL}/search.json"
                params['isbn'] = isbn
            elif title and author:
                search_url = f"{self.BASE_URL}/search.json"
                params['title'] = title
                params['author'] = author
            elif title:
                search_url = f"{self.BASE_URL}/search.json"
                params['title'] = title
            elif author:
                search_url = f"{self.BASE_URL}/search.json"
                params['author'] = author
            elif query:
                search_url = f"{self.BASE_URL}/search.json"
                params['q'] = query
            elif subject:
                search_url = f"{self.BASE_URL}/search.json"
                params['subject'] = subject
            else:
                return []

            params['limit'] = min(limit, 100)  # OpenLibrary max is 100
            params['fields'] = 'key,title,author_name,first_publish_year,isbn,cover_i,subject,publisher,number_of_pages_median,edition_count'

            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            results = []
            for doc in data.get('docs', []):
                book = self._parse_search_result(doc)
                results.append(book)

            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenLibrary search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in OpenLibrary search: {e}")
            return []

    def _parse_search_result(self, doc: Dict) -> Dict:
        """
        Parse OpenLibrary search result to standard format

        Args:
            doc: OpenLibrary document

        Returns:
            Parsed book in standard format
        """
        # Get cover ID
        cover_id = doc.get('cover_i')
        cover_url = None
        if cover_id:
            cover_url = f"{self.COVERS_URL}/b/id/{cover_id}-M.jpg"

        # Get authors
        authors = doc.get('author_name', [])
        author_str = ', '.join(authors) if authors else 'Unknown Author'

        # Get subjects
        subjects = doc.get('subject', [])
        subject_str = ', '.join(subjects[:3]) if subjects else ''

        return {
            'id': doc.get('key', '').replace('/works/', ''),
            'openlibrary_key': doc.get('key', ''),  # Full key like /works/OL123W
            'title': doc.get('title', 'Unknown Title'),
            'author': author_str,
            'first_publish_year': doc.get('first_publish_year'),
            'isbn': doc.get('isbn', [None])[0] if doc.get('isbn') else None,
            'cover_url': cover_url,
            'subject': subject_str,
            'publisher': doc.get('publisher', [None])[0] if doc.get('publisher') else None,
            'pages': doc.get('number_of_pages_median'),
            'editions': doc.get('edition_count', 0),
            'source': 'openlibrary',
            'relevance_score': 0.9,
            'retrieved_at': datetime.now().isoformat()
        }

    def get_book_details(self, work_id: str) -> Optional[Dict]:
        """
        Get detailed information about a book

        Args:
            work_id: OpenLibrary work ID

        Returns:
            Book details dictionary
        """
        try:
            # Handle both work IDs with and without /works/ prefix
            if not work_id.startswith('/works/'):
                work_id = f'/works/{work_id}'

            url = f"{self.BASE_URL}{work_id}.json"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # Get author information if available
            authors = []
            if 'authors' in data:
                for author_ref in data['authors']:
                    try:
                        author_url = f"{self.BASE_URL}{author_ref['author']['key']}.json"
                        author_response = self.session.get(author_url, timeout=self.timeout)
                        if author_response.status_code == 200:
                            author_data = author_response.json()
                            authors.append(author_data.get('name', 'Unknown'))
                    except Exception:
                        pass

            # Get cover ID
            covers = data.get('covers', [])
            cover_url = None
            if covers:
                cover_url = f"{self.COVERS_URL}/b/id/{covers[0]}-L.jpg"

            # Get subjects
            subjects = data.get('subjects', [])
            subject_str = ', '.join(subjects[:5]) if subjects else ''

            return {
                'id': work_id.replace('/works/', ''),
                'title': data.get('title', 'Unknown Title'),
                'author': ', '.join(authors) if authors else 'Unknown Author',
                'description': self._extract_description(data),
                'cover_url': cover_url,
                'subject': subject_str,
                'source': 'openlibrary',
                'retrieved_at': datetime.now().isoformat()
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenLibrary get details error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting book details: {e}")
            return None

    def _extract_description(self, data: Dict) -> str:
        """
        Extract description from OpenLibrary work data

        Args:
            data: Work data dictionary

        Returns:
            Description string
        """
        description = data.get('description')
        
        if isinstance(description, dict):
            return description.get('value', '')
        elif isinstance(description, str):
            return description
        
        return ''

    def check_availability(self, book_id: str) -> Dict:
        """
        Check availability (OpenLibrary doesn't have real-time availability)

        Args:
            book_id: Book ID

        Returns:
            Availability dictionary
        """
        # OpenLibrary is a catalog, not a lending library
        # Returns info about the book being available in the catalog
        return {
            'available': True,
            'message': 'Available in OpenLibrary catalog',
            'source': 'openlibrary'
        }

    def search_by_isbn(self, isbn: str) -> Optional[Dict]:
        """
        Search for a book by ISBN

        Args:
            isbn: ISBN code

        Returns:
            Book details or None
        """
        results = self.search(isbn=isbn, limit=1)
        return results[0] if results else None

    def get_book_by_isbn(self, isbn: str) -> Optional[Dict]:
        """
        Get detailed book information by ISBN using OpenLibrary's books API

        Args:
            isbn: ISBN-10 or ISBN-13 code

        Returns:
            Detailed book information or None
        """
        try:
            # Clean ISBN - remove dashes
            isbn = isbn.replace('-', '').replace(' ', '')
            
            # Use OpenLibrary's books API for detailed info
            url = f"{self.BASE_URL}/api/books"
            params = {
                'bibkeys': f'ISBN:{isbn}',
                'format': 'json',
                'jscmd': 'data'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            book_key = f'ISBN:{isbn}'
            if book_key not in data:
                logger.warning(f"No book found for ISBN: {isbn}")
                return None
            
            book_data = data[book_key]
            
            # Extract cover information
            cover_url = None
            if 'cover' in book_data:
                cover = book_data.get('cover', {})
                cover_url = cover.get('medium') or cover.get('small') or cover.get('large')
            
            # Extract authors
            authors = []
            if 'authors' in book_data:
                for author in book_data['authors']:
                    if isinstance(author, dict) and 'name' in author:
                        authors.append(author['name'])
                    elif isinstance(author, str):
                        authors.append(author)
            
            # Extract publishers
            publishers = []
            if 'publishers' in book_data:
                for pub in book_data['publishers']:
                    if isinstance(pub, dict) and 'name' in pub:
                        publishers.append(pub['name'])
                    elif isinstance(pub, str):
                        publishers.append(pub)
            
            # Extract subjects
            subjects = []
            if 'subjects' in book_data:
                for subject in book_data['subjects'][:10]:  # Limit to 10
                    if isinstance(subject, dict) and 'name' in subject:
                        subjects.append(subject['name'])
                    elif isinstance(subject, str):
                        subjects.append(subject)
            
            # Extract number of pages
            number_of_pages = book_data.get('number_of_pages') or book_data.get('pages')
            
            # Extract publish date
            publish_date = None
            if 'publish_date' in book_data:
                publish_date = book_data['publish_date']
            
            # Extract ISBNs
            isbns = []
            if 'isbn_13' in book_data:
                isbns.extend(book_data['isbn_13'])
            if 'isbn_10' in book_data:
                isbns.extend(book_data['isbn_10'])
            
            return {
                'id': f'isbn:{isbn}',
                'isbn': isbn,
                'title': book_data.get('title', 'Unknown Title'),
                'authors': authors,
                'author': ', '.join(authors) if authors else 'Unknown Author',
                'publishers': publishers,
                'publisher': publishers[0] if publishers else None,
                'publish_date': publish_date,
                'number_of_pages': number_of_pages,
                'subjects': subjects,
                'subject': ', '.join(subjects[:3]) if subjects else '',
                'cover_url': cover_url,
                'isbn_10': book_data.get('isbn_10', []),
                'isbn_13': book_data.get('isbn_13', []),
                'url': book_data.get('url'),
                'source': 'openlibrary',
                'retrieved_at': datetime.now().isoformat()
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenLibrary get book by ISBN error: {e}")
            # Fallback to search if API fails
            return self.search_by_isbn(isbn)
        except Exception as e:
            logger.error(f"Unexpected error getting book by ISBN: {e}")
            return self.search_by_isbn(isbn)