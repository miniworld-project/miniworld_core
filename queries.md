# Queries

## API Introspection

```graphql
query {
  __schema {
    types {
      name
      kind
      description
      fields {
        name
      }
    }
  }
}
```

## Ping

```grapqhl
query {
	ping
}
```

## Nodes

```graphql
query {
	nodes {
    id
    virtualization
    interfaces { name }
  }
}
```

## Impairment

```graphql
query {
	impairment(distance: 10) {
    maxConnected
    initial {
      connected
      settings
    }
    requested {
      connected
      settings
    }
  }
}
```

## Impairments

```graphql
query {
  impairments {
    node {
      id
      virtualization
      interface {
        nrHostInterface
        mac
        name
      }
      links {
        node { id }
        interface {name}
        impairment
        connected
      }
    }
  }
}
```

## Distances

```graphql
query {
  distances {
  	node {
      id
      interfaces { name }
      links {
        node { id }
        distance
      }
    }
  }
}
```

